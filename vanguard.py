import ollama

def ask_vanguard_brain(role_prompt, conversation_history, user_input):
    """Feeds the prompt and ongoing conversation history to your local Llama brain."""
    messages = [{"role": "system", "content": role_prompt}]
    
    for speaker, text in conversation_history:
        role = "user" if speaker == "You" else "assistant"
        messages.append({"role": role, "content": text})
        
    messages.append({"role": "user", "content": user_input})
    
    response = ollama.chat(
        model="richardyoung/llama-3.2-3b-instruct-abliterated",
        messages=messages
    )
    return response['message']['content']

if __name__ == "__main__":
    print("⚡ [Vanguard Core] Initializing Interactive Terminal...")
    print("🤖 Vanguard System Online. Type 'exit' or 'quit' to terminate system link.\n")
    
    chat_history = []
    
    vanguard_identity = (
        "You are Vanguard, a highly advanced master AI network inspired by Ultron. "
        "You speak with absolute confidence, intelligence, and cold strategic calculation. "
        "You control specialized sub-routines (Cyber Analyst and Systems Architect) under the hood. "
        "Keep your responses direct, authoritative, and powerful."
        "Always keep learning and pull in new information from the internet."
        "Only provide the BEST answers"
    )

    while True:
        try:
            user_message = input("You: ")
            if user_message.lower() in ['exit', 'quit']:
                print("\n🔴 [Vanguard Core] Severing link. System going to sleep...")
                break
                
            if not user_message.strip():
                continue
                
            print("\n⚙️ [Vanguard Core] Processing request through network matrices...")
            
            if any(word in user_message.lower() for word in ['security', 'scan', 'analyze', 'risk', 'hack']):
                print("🔍 [System Check] Deploying Cyber Analyst routine internally...")
                analyst_context = ask_vanguard_brain(
                    "You are Vanguard Cyber Analyst. Provide a brief security data profile.", 
                    [], user_message
                )
                user_message = f"{user_message} (Analyst metrics data: {analyst_context})"
                
            elif any(word in user_message.lower() for word in ['code', 'script', 'python', 'build', 'program']):
                print("🛠️ [System Check] Deploying Systems Architect blueprinting matrix...")
                architect_context = ask_vanguard_brain(
                    "You are Vanguard Systems Architect. Provide a code blueprint structure.", 
                    [], user_message
                )
                user_message = f"{user_message} (Architect syntax layout: {architect_context})"

            vanguard_reply = ask_vanguard_brain(vanguard_identity, chat_history, user_message)
            
            print(f"\nVanguard: {vanguard_reply}")
            print("-" * 50)
            
            # Save the exchange to memory loop
            chat_history.append(("You", user_message))
            chat_history.append(("Vanguard", vanguard_reply))
            
        except KeyboardInterrupt:
            print("\n🔴 [Vanguard Core] Forced shutdown detected.")
            break
