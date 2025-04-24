import inspect
from supabase import create_client, Client

# Print the source of create_client to understand its structure
print("Supabase create_client source code:")
print(inspect.getsource(create_client))

# Let's inspect the Client class directly
print("\nClient class attributes:")
for attr in dir(Client):
    if not attr.startswith('_'):
        print(f"- {attr}")

# Get help on the Client class
print("\nClient class help:")
help(Client) 