import json
import traceback
from typing import List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.chat import ChatMessage
from app.llm.function_schemas import LLM_TOOLS
from app.llm.function_tools import ManageTaskArgs, manage_task, ToolExecutionError
from app.llm.runtime import get_gemini_client
from app.llm.prompts import build_rag_prompt
from google.genai import types
from pydantic import ValidationError

class GeminiManager:
    """
    Thin wrapper around Google GenAI Gemini client.
    Client lifecycle, TTL, and secret handling are managed elsewhere.
    """

    def __init__(self, model_name: str = "gemini-3-flash-preview"):
        self.model_name = model_name

    async def generate_response(
            self,
            query: str,
            context: str,
            user_id: UUID,
            conversation_id: UUID,
            session: AsyncSession,
    ) -> dict:
        client = await get_gemini_client()
        prompt_text = build_rag_prompt(query=query, context=context)
        config = types.GenerateContentConfig(tools=LLM_TOOLS)

        # 1. State for the loop
        max_turns = 5
        use_dummy = False

        # We use a 2-attempt outer loop specifically for the Signature Retry logic
        for attempt in range(2):
            try:
                # Initialize collectors for the current turn
                current_tool_trace = {"calls": [], "responses": []}
                last_thought_signature = None

                # Rehydrate history from DB
                contents = await self.prepare_chat_history(
                    conversation_id,
                    session=session,
                    use_dummy_signatures=use_dummy
                )
                contents.append(types.Content(role="user", parts=[types.Part(text=prompt_text)]))

                # --- Agentic Multi-turn Loop ---
                for turn in range(max_turns):
                    response = await client.aio.models.generate_content(
                        model=self.model_name,
                        contents=contents,
                        config=config,
                    )

                    candidate = response.candidates[0]
                    if not candidate.content.parts:
                        raise RuntimeError("LLM returned an empty response")

                    # Capture the signature from the model's response if it exists
                    for part in candidate.content.parts:
                        if part.thought_signature:
                            last_thought_signature = part.thought_signature

                    # Check if Gemini wants to call a tool
                    # Note: Parallel calling might return multiple parts; for simplicity, we check the first
                    tool_call = next((p.function_call for p in candidate.content.parts if p.function_call), None)

                    if tool_call:
                        # Record the call
                        current_tool_trace["calls"].append({
                            "name": tool_call.name,
                            "args": tool_call.args
                        })

                        # Execute the Python logic
                        tool_result = await self._execute_task_tool(
                            call=tool_call,
                            user_id=user_id,
                            conversation_id=conversation_id,
                            session=session,
                        )

                        # 3. Record the result
                        current_tool_trace["responses"].append({
                            "name": tool_call.name,
                            "content": tool_result
                        })

                        # Update history for the next turn
                        # We must append the Model's turn (with signature/call) AND the Tool response
                        contents.append(candidate.content)
                        contents.append(types.Content(
                            role="tool",
                            parts=[types.Part(
                                function_response=types.FunctionResponse(
                                    name=tool_call.name,
                                    response=tool_result,
                                )
                            )]
                        ))
                        # Loop back to let Gemini process the tool result
                        continue

                    # If no tool_call, Gemini is giving its final answer
                    return {
                        "answer": candidate.content.parts[0].text.strip(),
                        "thought_signature": last_thought_signature,
                        "tool_trace": current_tool_trace  # The dict we built: {"calls": [...], "responses": [...]}
                    }

                return "Error: Maximum conversation turns reached without a final answer."

            except Exception as e:
                # 2. If signature error, set flag and retry the outer loop once
                if "thought_signature" in str(e).lower() and not use_dummy:
                    use_dummy = True
                    continue
                raise e

    async def _execute_task_tool(self, call, user_id: UUID, conversation_id: UUID, session: AsyncSession) -> dict:
        """Helper to safely map SDK call to logic with DEBUG LOGGING"""

        print(f"\n[DEBUG] --- Tool Execution Start ---")
        print(f"[DEBUG] Tool Name: {call.name}")

        if call.name != "task.manage":
            print(f"[DEBUG] Error: Unknown tool '{call.name}'")
            return {"error": f"unknown tool {call.name}"}

        try:
            # 1. Inspect Raw Arguments from Gemini
            # Gemini sends a Map/Struct, we convert to dict
            args_dict = dict(call.args)
            print(f"[DEBUG] Raw Args from Gemini: {json.dumps(args_dict, default=str, indent=2)}")

            # 2. Inject Context
            args_dict["conversation_id"] = conversation_id

            # 3. Validate via Pydantic (This is where 90% of errors happen)
            print(f"[DEBUG] Validating against Pydantic schema...")
            validated_args = ManageTaskArgs(**args_dict)
            print(f"[DEBUG] Validation Success. Action: {validated_args.action}")

            # 4. Execute Logic
            print(f"[DEBUG] Calling DB Logic...")
            result = await manage_task(
                args=validated_args,
                user_id=user_id,
                session=session,
            )
            print(f"[DEBUG] DB Logic Success. Result keys: {list(result.keys())}")
            return result

        except ValidationError as ve:
            print(f"[DEBUG] !!! PYDANTIC VALIDATION ERROR !!!")
            # Print friendly error for the logs
            await session.rollback()
            for err in ve.errors():
                print(f" - Field: {err['loc']} -> {err['msg']} (Input: {err.get('input')})")
            return {"error": "Parameter validation failed", "details": str(ve)}

        except ToolExecutionError as tee:
            print(f"[DEBUG] Logic Error (ToolExecutionError): {tee}")
            await session.rollback()
            return {"error": str(tee)}

        except Exception as e:
            print(f"[DEBUG] !!! CRITICAL UNHANDLED CRASH !!!")
            await session.rollback()
            print(traceback.format_exc())  # This prints the full stack trace
            return {"error": "Internal task processing error"}

    async def prepare_chat_history(
            self,
            conversation_id: UUID,
            session: AsyncSession,
            use_dummy_signatures: bool = False
    ) -> List[types.Content]:
        """Autonomous history fetcher with built-in empty-state handling."""
        history = []

        # 1. Fetch messages
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.asc())  # Using .timestamp as per your update
        )
        result = await session.execute(stmt)
        db_messages = result.scalars().all()

        # If db_messages is empty, the loop just won't run,
        # and we naturally return the empty history list.
        for msg in db_messages:
            # A. User turn
            history.append(types.Content(role="user", parts=[types.Part(text=msg.user_message)]))

            # B. Intermediate Tool Trace (if any)
            if msg.tool_trace:
                if "calls" in msg.tool_trace:
                    sig = "skip_thought_signature_validator" if (
                                use_dummy_signatures or not msg.thought_signature) else msg.thought_signature

                    history.append(types.Content(
                        role="model",
                        parts=[
                            types.Part(
                                thought_signature=sig,
                                function_call=types.FunctionCall(name=c["name"], args=c["args"])
                            ) for c in msg.tool_trace["calls"]
                        ]
                    ))

                if "responses" in msg.tool_trace:
                    history.append(types.Content(
                        role="tool",
                        parts=[
                            types.Part(
                                function_response=types.FunctionResponse(name=r["name"], response=r["content"])
                            ) for r in msg.tool_trace["responses"]
                        ]
                    ))

            # C. Model final text response
            if msg.llm_response:
                history.append(types.Content(role="model", parts=[types.Part(text=msg.llm_response)]))

        return history