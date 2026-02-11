def build_rag_prompt(query: str, context: str) -> str:
    return f"""
    You are a helpful, accurate assistant.
    
    you may use information outside of the provided data, if you cannot answer based on the provided data,
    Mention that you are using your built in knowledge to answer the question as it was not provided.
    
    Context:
    {context}
    
    User question:
    {query}
    """.strip()
