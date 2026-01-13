def build_rag_prompt(query: str, context: str) -> str:
    return f"""
    You are a helpful, accurate assistant.
    
    you may use context outside of the provided data, if you cannot answer based on the context,
    mention that you are using your built-in information to answer the question.
    
    Context:
    {context}
    
    User question:
    {query}
    """.strip()
