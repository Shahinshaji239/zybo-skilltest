import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import User, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        # Only allow authenticated users
        if not self.user.is_authenticated:
            await self.close()
            return

        self.other_user_id = self.scope['url_route']['kwargs']['user_id']
        
        # Create a unique room group name for these two users
        user_ids = sorted([self.user.id, int(self.other_user_id)])
        self.room_group_name = f'chat_{user_ids[0]}_{user_ids[1]}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Update user's online status
        await self.set_online_status(True)

    async def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

        if self.user.is_authenticated:
            await self.set_online_status(False)

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        action = text_data_json.get('action')

        if action == 'chat_message':
            message = text_data_json['message']
            if not message.strip():
                return # prevent empty messages

            # Save message to database
            msg_obj = await self.save_message(self.user.id, self.other_user_id, message)

            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': self.user.id,
                    'timestamp': msg_obj.timestamp.strftime('%H:%M'),
                    'msg_id': msg_obj.id
                }
            )
            
        elif action == 'mark_read':
            # Received signal from receiver that they read the message
            await self.mark_messages_read(self.other_user_id, self.user.id)
            
            # Broadcast read status back to sender
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'read_receipt',
                    'reader_id': self.user.id
                }
            )

        elif action == 'typing':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_typing',
                    'is_typing': text_data_json.get('is_typing', False),
                    'sender_id': self.user.id
                }
            )
            
        elif action == 'delete_message':
            msg_id = text_data_json.get('msg_id')
            if msg_id:
                success = await self.delete_message(msg_id, self.user.id)
                if success:
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'message_deleted',
                            'msg_id': msg_id
                        }
                    )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        sender_id = event['sender_id']
        timestamp = event['timestamp']
        msg_id = event['msg_id']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'action': 'chat_message',
            'message': message,
            'sender_id': sender_id,
            'timestamp': timestamp,
            'msg_id': msg_id
        }))

    async def read_receipt(self, event):
        reader_id = event['reader_id']
        await self.send(text_data=json.dumps({
            'action': 'read_receipt',
            'reader_id': reader_id
        }))

    async def user_typing(self, event):
        await self.send(text_data=json.dumps({
            'action': 'typing',
            'is_typing': event['is_typing'],
            'sender_id': event['sender_id']
        }))
        
    async def message_deleted(self, event):
        await self.send(text_data=json.dumps({
            'action': 'message_deleted',
            'msg_id': event['msg_id']
        }))

    @database_sync_to_async
    def set_online_status(self, is_online):
        User.objects.filter(id=self.user.id).update(
            is_online=is_online,
            last_seen=timezone.now() if not is_online else self.user.last_seen
        )

    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, content):
        return Message.objects.create(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content
        )

    @database_sync_to_async
    def mark_messages_read(self, sender_id, receiver_id):
        Message.objects.filter(sender_id=sender_id, receiver_id=receiver_id, is_read=False).update(is_read=True)

    @database_sync_to_async
    def delete_message(self, msg_id, user_id):
        try:
            msg = Message.objects.get(id=msg_id, sender_id=user_id)
            msg.delete()
            return True
        except Message.DoesNotExist:
            return False
