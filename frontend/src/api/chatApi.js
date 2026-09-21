import { apiClient } from './client';

export const chatApi = {
  // Send message to OIL HSE Safety Assistant
  sendMessage: (payload) =>
    apiClient.post('/chat', payload),

  // Get active conversations for current user
  getConversations: () =>
    apiClient.get('/chat/conversations'),

  // Get transcript of a conversation
  getConversationHistory: (conversationId) =>
    apiClient.get(`/chat/conversations/${conversationId}`),

  // Delete a conversation session
  deleteConversation: (conversationId) =>
    apiClient.delete(`/chat/conversations/${conversationId}`),
};
