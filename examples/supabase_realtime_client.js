// Supabase Realtime Chat Client Example
// This demonstrates how to connect to Supabase Realtime for chat functionality

// Import Supabase client
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase Client - replace with your project URL and anon key
const supabaseUrl = 'https://qbhevelbszcvxkutfmlg.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFiaGV2ZWxic3pjdnhrdXRmbWxnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDMxMDIzOTEsImV4cCI6MjA1ODY3ODM5MX0.oZCcntSOuqx4neB58s_5kUeIGt-xWm1AqFoEQP6UUn8';
const supabase = createClient(supabaseUrl, supabaseAnonKey);

// API endpoint
const API_URL = 'http://localhost:8081';

// Example JWT token for authentication - you would get this from your auth system
let token = null;

// Chat functions
class ChatClient {
  constructor() {
    this.conversationId = null;
    this.channel = null;
  }

  // Login and get token
  async login(email, password) {
    try {
      // This uses Supabase Auth, but you might have your own auth system
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) throw error;
      
      token = data.session.access_token;
      console.log('Logged in successfully');
      return true;
    } catch (error) {
      console.error('Login error:', error.message);
      return false;
    }
  }

  // Create a new conversation
  async createConversation(botId) {
    try {
      const response = await fetch(`${API_URL}/api/chat/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ bot_id: botId })
      });

      if (!response.ok) throw new Error('Failed to create conversation');
      
      const data = await response.json();
      this.conversationId = data.id;
      console.log(`Conversation created with ID: ${this.conversationId}`);
      return this.conversationId;
    } catch (error) {
      console.error('Create conversation error:', error.message);
      throw error;
    }
  }

  // Subscribe to realtime updates for a conversation
  async subscribeToConversation(conversationId) {
    try {
      this.conversationId = conversationId;
      
      // Create the channel
      const channelName = `conversation:${conversationId}`;
      this.channel = supabase.channel(channelName);
      
      // Listen for new messages using Postgres Changes
      this.channel
        .on(
          'postgres_changes',
          {
            event: 'INSERT',
            schema: 'public',
            table: 'messages',
            filter: `conversation_id=eq.${conversationId}`
          },
          (payload) => {
            console.log('New message received:', payload.new);
            // Call your message display function here
            this.onMessageReceived(payload.new);
          }
        )
        // Listen for typing indicators using broadcast
        .on(
          'broadcast',
          { event: 'typing' },
          (payload) => {
            console.log('Typing indicator:', payload);
            // Update UI to show typing indicator
            this.onTypingIndicator(payload);
          }
        )
        .subscribe();
      
      console.log(`Subscribed to conversation: ${conversationId}`);
      return true;
    } catch (error) {
      console.error('Subscribe error:', error.message);
      return false;
    }
  }

  // Send a message to the conversation
  async sendMessage(content) {
    try {
      if (!this.conversationId) {
        throw new Error('No active conversation');
      }

      const response = await fetch(`${API_URL}/api/chat/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          conversation_id: this.conversationId,
          sender_type: 'user',
          content
        })
      });

      if (!response.ok) throw new Error('Failed to send message');
      
      const data = await response.json();
      console.log('Message sent:', data);
      return data;
    } catch (error) {
      console.error('Send message error:', error.message);
      throw error;
    }
  }

  // Send typing indicator
  async sendTypingIndicator(isTyping) {
    try {
      if (!this.conversationId) {
        throw new Error('No active conversation');
      }

      const response = await fetch(`${API_URL}/api/chat/typing?conversation_id=${this.conversationId}&is_typing=${isTyping}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Failed to send typing indicator');
      
      console.log(`Typing indicator (${isTyping}) sent`);
      return true;
    } catch (error) {
      console.error('Typing indicator error:', error.message);
      return false;
    }
  }

  // Fetch message history
  async getMessageHistory(limit = 50) {
    try {
      if (!this.conversationId) {
        throw new Error('No active conversation');
      }

      const response = await fetch(`${API_URL}/api/chat/messages/${this.conversationId}?limit=${limit}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch messages');
      
      const data = await response.json();
      console.log(`Fetched ${data.length} messages`);
      return data;
    } catch (error) {
      console.error('Get messages error:', error.message);
      throw error;
    }
  }

  // Unsubscribe from the channel
  unsubscribe() {
    if (this.channel) {
      this.channel.unsubscribe();
      console.log('Unsubscribed from channel');
    }
  }

  // Callback when new message is received
  onMessageReceived(message) {
    // Override this method in your application
    console.log(`Message from ${message.sender_type}: ${message.content}`);
  }

  // Callback when typing indicator is received
  onTypingIndicator(data) {
    // Override this method in your application
    const { user_id, is_typing } = data.payload;
    console.log(`User ${user_id} is ${is_typing ? 'typing' : 'not typing'}`);
  }
}

// Usage example
async function demoChat() {
  const chat = new ChatClient();
  
  // Login (replace with actual credentials)
  await chat.login('user@example.com', 'password123');
  
  // Create a conversation with bot-123
  const conversationId = await chat.createConversation('bot-123');
  
  // Subscribe to real-time updates
  await chat.subscribeToConversation(conversationId);
  
  // Override message received callback
  chat.onMessageReceived = (message) => {
    const sender = message.sender_type === 'user' ? 'You' : 'Bot';
    console.log(`${sender}: ${message.content}`);
    
    // If citations exist, show them
    if (message.citations && message.citations.length > 0) {
      console.log('Citations:');
      message.citations.forEach(citation => {
        console.log(`- ${citation.title}: ${citation.text}`);
      });
    }
  };
  
  // Send typing indicator
  await chat.sendTypingIndicator(true);
  
  // Simulate typing delay
  setTimeout(async () => {
    // Send a message
    await chat.sendMessage('Hello, I have a question about your products');
    
    // Stop typing indicator
    await chat.sendTypingIndicator(false);
  }, 2000);
  
  // Cleanup on page unload
  window.addEventListener('beforeunload', () => {
    chat.unsubscribe();
  });
}

// Run the demo
// demoChat().catch(console.error);

// Export for usage in other files
export default ChatClient; 