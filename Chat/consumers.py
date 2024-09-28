import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from Chat.models import *
import base64
from django.core.files.base import ContentFile

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = f"room_{self.scope['url_route']['kwargs']['room_id']}"
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()
        
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_payload_data = text_data_json

        event = {
            'type': 'send_message',
            'message_payload': message_payload_data,
        }

        await self.channel_layer.group_send(self.room_name, event)

        # content, image, room id, sender

    async def send_message(self, event):

        data = event['message_payload']
        await self.create_message(data=data)

        response_data = {
            'sender': data['sender_id'],
            'message': data['message']
        }
        if data.get("image"):
            response_data['image'] = data['image']
        await self.send(text_data=json.dumps({'message': response_data}))

    @database_sync_to_async
    def create_message(self, data):

        room_id = data["room_id"]
        sender_id = data["sender_id"]
        message = data["message"]
        image_data = data.get("image")

        chat_room = ChatRoom.objects.get(id=int(room_id))
        message_sender = User.objects.get(id=int(sender_id))
        
        if not Message.objects.filter(content=message).exists():
            new_message = Message(chat_room=chat_room, sender=message_sender, content=message)
            if image_data:
                # If image is present, process it
                format, imgstr = image_data.split(';base64,')  # Split the base64 string
                ext = format.split('/')[-1]  # Extract image extension
                image_file = ContentFile(base64.b64decode(imgstr), name=f'{sender_id}_{room_id}.{ext}')
                new_message.image = image_file
                new_message.contains_image = True
            new_message.save()  
        