import os
import requests
from dotenv import load_dotenv
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys # Added for specific key handling
from rich.console import Console
from rich.markdown import Markdown

def chat_with_llm(api_key, messages):
    """Sends messages to the LLM and returns the response."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "deepseek-reasoner",  # Or any other model you prefer
        "messages": messages,
    }
    response = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=data)
    response.raise_for_status()  # Raise an exception for bad status codes
    return response.json()["choices"][0]["message"]["content"]

def main():
    """Main function to run the chat interface."""
    load_dotenv()
    api_key = os.getenv("DEEPSEEK_API_KEY")

    if not api_key:
        print("Error: DEEPSEEK_API_KEY not found in .env file.")
        return

    console = Console() # Initialize Rich console

    # Setup key bindings for prompt_toolkit (for the edit prompt)
    kb_edit = KeyBindings()

    @kb_edit.add('-')
    def _(event):
        """
        Delete 25 characters before the cursor.
        """
        event.app.current_buffer.delete_before_cursor(count=15)

    @kb_edit.add('=') # Changed from '+' to '='
    def _(event):
        """
        Insert a newline character.
        """
        event.app.current_buffer.insert_text('\n') # Corrected to insert an actual newline

    print("start")
    messages = []

    while True:
        print() # Add a newline before user input
        user_input = input("You: ") # Standard input for user's message
        if user_input.lower() == "quit":
            break

        messages.append({"role": "user", "content": user_input})

        try:
            llm_response = chat_with_llm(api_key, messages)
            
            print() # Add a newline before LLM output
            # Display the richly formatted response first
            console.print(f"LLM: ", end="")
            console.print(Markdown(llm_response))

            # Decision prompt: Edit or Continue?
            kb_decide = KeyBindings()
            
            @kb_decide.add(Keys.Enter)
            def _(event):
                event.app.exit(result="continue")

            @kb_decide.add(Keys.Backspace)
            def _(event):
                # We don't want Backspace to delete characters in this specific prompt,
                # just trigger the edit action.
                event.app.exit(result="edit")

            decision = prompt("Press Enter to continue, Backspace to edit response: ", key_bindings=kb_decide)

            final_llm_response = llm_response 

            if decision == "edit":
                # Show plain version for editing, using the kb_edit for '-' and '=' functionality
                edited_response = prompt(f"Edit LLM\\\\\\'s response: ", default=llm_response, key_bindings=kb_edit)
                final_llm_response = edited_response
            
            messages.append({"role": "assistant", "content": final_llm_response})

        except requests.exceptions.RequestException as e:
            print(f"Error communicating with LLM: {e}")
            # Remove the last user message if the API call failed
            messages.pop()


if __name__ == "__main__":
    main()