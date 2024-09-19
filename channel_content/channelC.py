from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
import json

API_ID = 28870257  # Tvoj API ID
API_HASH = 'e1438d4646b0028850650fcc9c73b058'  # Tvoj API HASH
phone = '+421949550035'  # Tvoje telefónne číslo

client = TelegramClient('my-client', API_ID, API_HASH)

client.connect()
if not client.is_user_authorized():
    client.send_code_request(phone)
    client.sign_in(phone, input('Enter the code: '))

chats = []
last_date = None
chunk_size = 200
groups = []

# Získanie zoznamu všetkých skupín
result = client(GetDialogsRequest(
    offset_date=last_date,
    offset_id=0,
    offset_peer=InputPeerEmpty(),
    limit=chunk_size,
    hash=0
))
chats.extend(result.chats)

# Tu sa nezameriavame len na megagroups, vypíšeme všetky typy skupín
print('All available chats:')
for chat in chats:
    print(f"Chat: {chat.title}, is_megagroup: {getattr(chat, 'megagroup', False)}")
    groups.append(chat)  # Pridaj všetky skupiny bez ohľadu na typ

# Zobraz výber skupiny na stiahnutie členov a správ
print('Choose a group to scrape members and messages from:')
for i, g in enumerate(groups):
    print(f"{i} | {g.title}")

g_index = input("Enter a Number: ")
target_group = groups[int(g_index)]

print('Fetching Members and Messages...')
all_participants = client.get_participants(target_group, aggressive=True)

# Uloženie údajov do JSON súboru
print('Saving In file...')
members_data = []

async def fetch_messages_for_user(user):
    """Funkcia na získanie správ pre konkrétneho používateľa"""
    messages = []
    async for message in client.iter_messages(target_group, from_user=user):
        # Kontrola, či má správa text, ak nie, zobrazí sa ako 'No text available'
        message_text = message.text if message.text else 'No text available'
        messages.append({
            "message_id": message.id,
            "text": message_text,
            "date": str(message.date)
        })
    return messages

async def main():
    """Hlavná funkcia na spracovanie členov a ich správ"""
    for user in all_participants:
        username = user.username if user.username else ""
        first_name = user.first_name if user.first_name else ""
        last_name = user.last_name if user.last_name else ""
        name = (first_name + ' ' + last_name).strip()

        # Získanie správ pre konkrétneho používateľa
        messages = await fetch_messages_for_user(user)

        member_info = {
            "username": username,
            "user_id": user.id,
            "access_hash": user.access_hash,
            "name": name,
            "group": target_group.title,
            "group_id": target_group.id,
            "messages": messages  # Pridanie správ používateľa
        }

        members_data.append(member_info)

    # Zapíše údaje do JSON súboru
    with open("members_with_messages.json", "w", encoding="UTF-8") as f:
        json.dump(members_data, f, ensure_ascii=False, indent=4)

    print('Members and their messages scraped and saved to members_with_messages.json successfully.')

# Spustenie hlavnej funkcie
with client:
    client.loop.run_until_complete(main())
