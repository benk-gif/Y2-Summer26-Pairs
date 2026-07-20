
import app1
import app2

def main():
    
    shared_history = []

    current_agent = input(
        "Choose an agent to start ('ben': routes, 'june': concerts): "
    ).strip().lower()

    while True:
        if current_agent == "ben":
            
            current_agent = app2.run_chat(shared_history)
        elif current_agent == "june":
            
            current_agent = app1.run_chat(shared_history)
        elif current_agent == "exit":
            print("Exiting program. Goodbye!")
            break
        else:
            current_agent = input("Invalid option. Enter 'ben', 'june', or 'exit': ").strip().lower()

if __name__ == "__main__":
    main()