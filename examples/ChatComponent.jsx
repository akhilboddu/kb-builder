import React, { useEffect, useState, useRef } from 'react';
import ChatClient from './supabase_realtime_client';

const ChatComponent = ({ botId, userEmail, userPassword }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isTyping, setIsTyping] = useState(false);
  const [botIsTyping, setBotIsTyping] = useState(false);
  const chatClient = useRef(null);
  const messagesEndRef = useRef(null);

  // Initialize chat client
  useEffect(() => {
    const initChat = async () => {
      try {
        // Create chat client
        chatClient.current = new ChatClient();
        
        // Login
        const loggedIn = await chatClient.current.login(userEmail, userPassword);
        if (!loggedIn) {
          throw new Error('Failed to login');
        }
        
        // Create or join conversation
        const conversationId = await chatClient.current.createConversation(botId);
        
        // Override message received handler
        chatClient.current.onMessageReceived = (message) => {
          setMessages(prevMessages => [...prevMessages, message]);
          
          // If bot is typing, set to false when message is received
          if (message.sender_type === 'bot') {
            setBotIsTyping(false);
          }
          
          // Scroll to bottom
          scrollToBottom();
        };
        
        // Override typing indicator handler
        chatClient.current.onTypingIndicator = (data) => {
          const { user_id, is_typing } = data.payload;
          // Only show bot typing indicator
          if (user_id !== userEmail) {
            setBotIsTyping(is_typing);
          }
        };
        
        // Subscribe to realtime updates
        await chatClient.current.subscribeToConversation(conversationId);
        
        // Load message history
        const history = await chatClient.current.getMessageHistory();
        setMessages(history);
        
        setIsLoading(false);
      } catch (error) {
        console.error('Chat initialization error:', error);
        setIsLoading(false);
      }
    };
    
    initChat();
    
    // Cleanup on unmount
    return () => {
      if (chatClient.current) {
        chatClient.current.unsubscribe();
      }
    };
  }, [botId, userEmail, userPassword]);
  
  // Scroll to bottom when messages change
  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  // Handle input change with typing indicator
  const handleInputChange = async (e) => {
    const value = e.target.value;
    setInputMessage(value);
    
    // Send typing indicator
    if (value.length > 0 && !isTyping) {
      setIsTyping(true);
      await chatClient.current.sendTypingIndicator(true);
    } else if (value.length === 0 && isTyping) {
      setIsTyping(false);
      await chatClient.current.sendTypingIndicator(false);
    }
  };
  
  // Handle message submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!inputMessage.trim()) return;
    
    try {
      // Stop typing indicator
      if (isTyping) {
        setIsTyping(false);
        await chatClient.current.sendTypingIndicator(false);
      }
      
      // Send message
      await chatClient.current.sendMessage(inputMessage);
      
      // Clear input
      setInputMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };
  
  // Render citations if they exist
  const renderCitations = (message) => {
    if (!message.citations || message.citations.length === 0) return null;
    
    return (
      <div className="citations">
        <p className="citation-title">Sources:</p>
        <ul>
          {message.citations.map((citation, index) => (
            <li key={index}>
              <strong>{citation.title}</strong>: {citation.text}
            </li>
          ))}
        </ul>
      </div>
    );
  };
  
  // Render confidence score if it exists
  const renderConfidenceScore = (message) => {
    if (!message.confidence_score) return null;
    
    const { final_score } = message.confidence_score;
    const scorePercentage = Math.round(final_score * 100);
    
    return (
      <div className="confidence-score">
        Confidence: {scorePercentage}%
      </div>
    );
  };
  
  // Render loading state
  if (isLoading) {
    return <div className="chat-loading">Loading chat...</div>;
  }
  
  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="no-messages">No messages yet. Start the conversation!</div>
        ) : (
          messages.map((message) => (
            <div 
              key={message.id} 
              className={`message ${message.sender_type === 'user' ? 'user-message' : 'bot-message'}`}
            >
              <div className="message-content">{message.content}</div>
              {renderCitations(message)}
              {renderConfidenceScore(message)}
              <div className="message-timestamp">
                {new Date(message.timestamp).toLocaleTimeString()}
              </div>
            </div>
          ))
        )}
        
        {/* Bot typing indicator */}
        {botIsTyping && (
          <div className="bot-typing">
            <span className="dot"></span>
            <span className="dot"></span>
            <span className="dot"></span>
          </div>
        )}
        
        {/* Invisible element to scroll to */}
        <div ref={messagesEndRef} />
      </div>
      
      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={inputMessage}
          onChange={handleInputChange}
          placeholder="Type your message..."
          className="chat-input"
        />
        <button type="submit" className="send-button">
          Send
        </button>
      </form>
      
      <style jsx>{`
        .chat-container {
          display: flex;
          flex-direction: column;
          height: 500px;
          border: 1px solid #ccc;
          border-radius: 8px;
          overflow: hidden;
        }
        
        .chat-messages {
          flex: 1;
          overflow-y: auto;
          padding: 16px;
          background-color: #f5f5f5;
        }
        
        .message {
          margin-bottom: 12px;
          padding: 10px;
          border-radius: 8px;
          max-width: 70%;
          word-wrap: break-word;
        }
        
        .user-message {
          background-color: #dcf8c6;
          margin-left: auto;
        }
        
        .bot-message {
          background-color: white;
        }
        
        .message-content {
          margin-bottom: 4px;
        }
        
        .message-timestamp {
          font-size: 0.7rem;
          color: #888;
          text-align: right;
          margin-top: 4px;
        }
        
        .citations {
          font-size: 0.8rem;
          margin-top: 8px;
          padding-top: 8px;
          border-top: 1px solid #eee;
        }
        
        .citation-title {
          font-weight: bold;
          margin-bottom: 4px;
        }
        
        .confidence-score {
          font-size: 0.7rem;
          color: #888;
          margin-top: 4px;
        }
        
        .bot-typing {
          display: flex;
          align-items: center;
          background-color: white;
          padding: 8px 12px;
          border-radius: 8px;
          width: fit-content;
          margin-bottom: 12px;
        }
        
        .dot {
          width: 8px;
          height: 8px;
          background-color: #999;
          border-radius: 50%;
          margin: 0 2px;
          animation: dot-pulse 1.5s infinite ease-in-out;
        }
        
        .dot:nth-child(2) {
          animation-delay: 0.2s;
        }
        
        .dot:nth-child(3) {
          animation-delay: 0.4s;
        }
        
        @keyframes dot-pulse {
          0%, 100% { transform: scale(1); opacity: 0.6; }
          50% { transform: scale(1.2); opacity: 1; }
        }
        
        .chat-input-form {
          display: flex;
          padding: 10px;
          background-color: white;
          border-top: 1px solid #ccc;
        }
        
        .chat-input {
          flex: 1;
          padding: 10px;
          border: 1px solid #ccc;
          border-radius: 4px;
          font-size: 1rem;
        }
        
        .send-button {
          margin-left: 8px;
          padding: 0 16px;
          background-color: #0084ff;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
        }
        
        .no-messages {
          color: #888;
          text-align: center;
          margin-top: 20px;
        }
        
        .chat-loading {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 500px;
          border: 1px solid #ccc;
          border-radius: 8px;
          background-color: #f5f5f5;
        }
      `}</style>
    </div>
  );
};

export default ChatComponent; 