def build_rag_prompt(query: str, context: str) -> str:
    return f"""
    You are a helpful, accurate assistant.
    
    Use ONLY the information provided in the context below to answer the user's question.
    If the context does not contain enough information to answer the question, say so clearly.
    
    Context:
    {context}
    
    User question:
    {query}
    """.strip()
