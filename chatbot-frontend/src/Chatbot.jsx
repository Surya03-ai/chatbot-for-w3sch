import { useState, useRef, useEffect, useCallback } from 'react';
import './index.css';

const BOT_NAME = 'W3Guide AI';
const BOT_ICON = '🧠';
const USER_ICON = '🧑‍💻';

const formatTimestamp = () =>
  new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

const createMessage = (text, isUser) => ({
  id: `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`,
  text,
  isUser,
  timestamp: formatTimestamp()
});

const chatbotKnowledge = [
  {
    keywords: ['hello', 'hi', 'hey'],
    response: 'Hello! How can I help you learn web development today?'
  },
  {
    keywords: ['css'],
    response: 'CSS: Need help with Flexbox, Grid, animations, or responsive design?'
  },
  {
    keywords: ['javascript', 'js'],
    response: 'JavaScript: Ask about DOM manipulation, events, async/await, or frameworks!'
  },
  {
    keywords: ['html'],
    response: 'HTML: Semantic elements, forms, accessibility, or HTML5 features?'
  },
  {
    keywords: ['react'],
    response: 'React: Components, hooks, state, props, or routing questions?'
  }
];

const generateBotResponse = (userMessage) => {
  const normalized = userMessage.toLowerCase().trim();

  const knowledge = chatbotKnowledge.find(({ keywords }) =>
    keywords.some((keyword) => normalized.includes(keyword))
  );

  return (
    knowledge?.response ||
    'Great question! I can help with HTML, CSS, JavaScript, React, Python, SQL and more. What specific topic would you like help with?'
  );
};

const TypingIndicator = () => (
  <div className="flex justify-start animate-slide-in">
    <div className="bg-[#D9EEE1] border border-emerald-200 rounded-xl px-4 py-3 max-w-[85%] shadow-sm flex items-center gap-2">
      <span className="text-lg flex-shrink-0">{BOT_ICON}</span>
      <div className="flex items-center gap-0.5">
        <div className="typing-blink w-2 h-2 bg-emerald-600 rounded-full"></div>
        <div className="typing-dots delay-100 w-2 h-2 bg-emerald-600 rounded-full"></div>
        <div className="typing-blink delay-200 w-2 h-2 bg-emerald-600 rounded-full"></div>
      </div>
      <span className="text-xs font-medium text-emerald-800 whitespace-nowrap">
        Bot is typing...
      </span>
    </div>
  </div>
);

const MessageBubble = ({ message }) => (
  <div
    key={message.id}
    className={`flex ${message.isUser ? 'justify-end' : 'justify-start'} animate-slide-in`}
  >
    <div
      className={`max-w-[85%] p-4 rounded-xl shadow-sm flex items-start gap-2 ${
        message.isUser
          ? 'bg-white border border-gray-200 rounded-br-none ml-auto'
          : 'bg-[#D9EEE1] border border-emerald-200 rounded-bl-none'
      }`}
    >
      <span className="text-lg mt-1 flex-shrink-0">{message.isUser ? USER_ICON : BOT_ICON}</span>
      <div className="flex-1 min-w-0">
        <p className="text-sm leading-relaxed text-gray-800 break-words font-medium">{message.text}</p>
        <p className="text-xs text-gray-500 mt-1.5 font-mono tracking-wide">{message.timestamp}</p>
      </div>
    </div>
  </div>
);

const ChatInput = ({ input, onChange, onSubmit, onKeyDown, isTyping }) => (
  <div className="p-5 bg-white border-t border-gray-100 flex-shrink-0 rounded-b-2xl">
    <form onSubmit={onSubmit} className="flex gap-3 items-end">
      <input
        value={input}
        onChange={onChange}
        onKeyDown={onKeyDown}
        placeholder="Type your question... (HTML, CSS, JS...)"
        className="flex-1 px-4 py-3 border border-gray-300 rounded-xl text-sm font-medium text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#04AA6D]/50 focus:border-[#04AA6D] transition-all duration-200 bg-white shadow-sm disabled:opacity-50"
        disabled={isTyping}
        autoFocus
        maxLength={500}
      />
      <button
        type="submit"
        disabled={!input.trim() || isTyping}
        className="w-14 h-14 bg-[#04AA6D] hover:bg-[#059862] active:bg-[#048f5d] disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-xl shadow-lg hover:shadow-xl active:scale-[0.98] transition-all duration-200 flex items-center justify-center flex-shrink-0 font-semibold"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
      </button>
    </form>
  </div>
);

const Chatbot = () => {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      text:
        "Hi! I'm W3Guide AI. Ask me about HTML, CSS, JavaScript or any web development topic!",
      isUser: false,
      timestamp: formatTimestamp()
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const messagesEndRef = useRef(null);
  const timeoutRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  const addMessage = useCallback((message) => {
    setMessages((prev) => [...prev, message]);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, scrollToBottom]);

  useEffect(() => {
    return () => clearTimeout(timeoutRef.current);
  }, []);

  const toggleChat = () => setIsOpen((prev) => !prev);

  const handleSend = useCallback(() => {
    const trimmedMessage = input.trim();
    if (!trimmedMessage || isTyping) return;

    const userMessage = createMessage(trimmedMessage, true);
    addMessage(userMessage);
    setInput('');
    setIsTyping(true);

    timeoutRef.current = setTimeout(() => {
      const botMessage = createMessage(generateBotResponse(trimmedMessage), false);
      addMessage(botMessage);
      setIsTyping(false);
    }, 1000);
  }, [input, isTyping, addMessage]);

  const handleSubmit = (event) => {
    event.preventDefault();
    handleSend();
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={toggleChat}
        className="fixed bottom-6 right-6 z-[10000] w-14 h-14 rounded-full bg-[#04AA6D] hover:bg-[#059862] shadow-lg hover:shadow-xl active:scale-[0.97] transition-all duration-200 flex items-center justify-center text-white text-xl font-bold border-4 border-white focus:outline-none focus:ring-4 focus:ring-green-300"
        aria-label={`Open ${BOT_NAME} chatbot`}
        title={`Open ${BOT_NAME}`}
      >
        💬
      </button>
    );
  }

  return (
    <>
      <div className="fixed inset-0 z-[9999] bg-black/10" onClick={toggleChat} />

      <div
        className="fixed z-[10000] bottom-6 right-6 w-[350px] h-[500px] bg-white border border-gray-200 rounded-2xl shadow-2xl hover:shadow-3xl transition-all duration-200 flex flex-col max-h-[90vh]"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="bg-[#04AA6D] px-6 py-4 rounded-t-2xl flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
              <span className="text-lg font-bold">{BOT_ICON}</span>
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">{BOT_NAME}</h3>
              <span className="text-xs bg-white/20 px-2.5 py-0.5 rounded-full text-white font-medium">
                Online
              </span>
            </div>
          </div>
          <button
            onClick={toggleChat}
            className="p-1.5 rounded-xl hover:bg-white/30 transition-all duration-200 text-white/90 hover:text-white hover:scale-105"
            aria-label="Close chatbot"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 bg-gray-50 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4 chat-scroll-light">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}

            {isTyping && <TypingIndicator />}

            <div ref={messagesEndRef} />
          </div>
        </div>

        <ChatInput
          input={input}
        onChange={(event) => setInput(event.target.value)}
        onSubmit={handleSubmit}
        onKeyDown={handleKeyDown}
        isTyping={isTyping}
      />
      </div>
    </>
  );
};

export default Chatbot;
