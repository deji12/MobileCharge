from django.db import models
from Authentication.models import User

class ChatRoom(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    def get_messages(self):
        return Message.objects.filter(chat_room=self)
    
    def get_last_message(self):
        return Message.objects.filter(chat_room=self).order_by('-date_and_time_of_message_send').first()

class Message(models.Model):

    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sender")
    content = models.TextField(null=True, blank=True)
    contains_image = models.BooleanField(default=False)
    image = models.FileField(upload_to='images/chat', null=True, blank=True)
    date_and_time_of_message_send = models.DateTimeField(auto_now_add=True)