import { useState, useEffect, useRef, useMemo } from 'react';
import { X, Send, Sparkles, Bot } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { Button } from './ui/button';
import { calculateTransitionMetrics, formatDate } from '../utils/dataLoader';
import type { Company, CEOTransition, StockData } from '../utils/types';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

interface ChatBotProps {
  currentView: 'home' | 'selector' | 'analysis';
  company: Company | null;
  transition: CEOTransition | null;
  stockData: StockData | null;
}

export function ChatBot({ currentView, company, transition, stockData }: ChatBotProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      text: "Hello! I'm your CEO Transition Analyst. Ask me anything about the data you're viewing.",
      sender: 'bot',
      timestamp: new Date()
    }
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, isOpen]);

  // Calculate metrics for chat responses
  const metrics = useMemo(() => {
    if (!stockData || !transition) return null;
    return calculateTransitionMetrics(stockData.data, transition.transitionDate);
  }, [stockData, transition]);

  // Generate response based on context
  const generateResponse = (query: string) => {
    const lowerQuery = query.toLowerCase();

    // General greetings
    if (lowerQuery.includes('hello') || lowerQuery.includes('hi') || lowerQuery.includes('hey')) {
      return "Hello! How can I help you analyze the CEO transition data today?";
    }

    if (currentView === 'home') {
      if (lowerQuery.includes('what') && (lowerQuery.includes('do') || lowerQuery.includes('this'))) {
        return "This tool analyzes the impact of CEO transitions on stock market performance. Click **Start Analysis** to select a company and explore how leadership changes affected stock prices.";
      }
      if (lowerQuery.includes('how') && lowerQuery.includes('work')) {
        return "We use SEC 10-K filings to detect CEO changes and combine that with daily stock price data spanning 30 years (1996-2025). Select a company, pick a transition, and get detailed charts and metrics.";
      }
      return "You're on the Home page. Click **Start Analysis** to select a company and begin exploring CEO transition data.";
    }

    if (currentView === 'selector') {
      if (lowerQuery.includes('how') && lowerQuery.includes('select')) {
        return "Browse the company list on the left, or use the search bar to find a specific company by name or ticker. Then select a CEO transition from the right panel and click **Analyze Transition**.";
      }
      return "You're selecting a company. Use the search and filters to find a company, then pick a CEO transition to analyze.";
    }

    if (currentView === 'analysis' && company && transition) {
      // CEO questions
      if (lowerQuery.includes('who') && (lowerQuery.includes('ceo') || lowerQuery.includes('new') || lowerQuery.includes('incoming'))) {
        return `The incoming CEO is **${transition.newCEO}**, who took over from **${transition.previousCEO}** at ${company.name}.`;
      }

      if (lowerQuery.includes('previous') || lowerQuery.includes('outgoing') || lowerQuery.includes('old ceo')) {
        return `The outgoing CEO was **${transition.previousCEO}**. Their last 10-K filing was on ${formatDate(transition.filingBefore)}.`;
      }

      // Impact / stock performance questions
      if (lowerQuery.includes('impact') || lowerQuery.includes('performance') || (lowerQuery.includes('stock') && !lowerQuery.includes('price'))) {
        if (metrics && metrics.impact90Days !== null) {
          const dir = metrics.impact90Days >= 0 ? 'increased' : 'decreased';
          let response = `Following the CEO transition, ${company.name}'s stock **${dir} by ${Math.abs(metrics.impact90Days).toFixed(1)}%** over 90 days.`;
          if (metrics.impact1Year !== null) {
            const dir1y = metrics.impact1Year >= 0 ? 'gained' : 'lost';
            response += ` Over 1 year, the stock **${dir1y} ${Math.abs(metrics.impact1Year).toFixed(1)}%**.`;
          }
          return response;
        }
        return "Insufficient stock data to calculate the impact for this transition period.";
      }

      // Price questions
      if (lowerQuery.includes('price')) {
        if (metrics?.priceAtTransition) {
          return `The stock price around the transition date was approximately **$${metrics.priceAtTransition.toFixed(2)}** (adjusted close).`;
        }
        return "Price data is not available for the exact transition date.";
      }

      // Volatility questions
      if (lowerQuery.includes('volatil') || lowerQuery.includes('risk')) {
        if (metrics) {
          return `The annualized volatility around this transition was **${metrics.volatility.toFixed(1)}%**, which is considered **${metrics.volatilityLevel}** risk.`;
        }
        return "Volatility data is not available for this transition.";
      }

      // Date / when questions
      if (lowerQuery.includes('when') || lowerQuery.includes('date') || lowerQuery.includes('transition date')) {
        return `The CEO transition is estimated to have occurred around **${formatDate(transition.transitionDate)}**, based on SEC 10-K filing records. The last filing by ${transition.previousCEO} was on ${formatDate(transition.filingBefore)}, and the first filing by ${transition.newCEO} was on ${formatDate(transition.filingAfter)}.`;
      }

      // Company info
      if (lowerQuery.includes('company') || lowerQuery.includes('sector') || lowerQuery.includes('about')) {
        return `**${company.name}** (${company.ticker}) is in the **${company.sector}** sector. It has had **${company.transitionCount}** CEO transition${company.transitionCount !== 1 ? 's' : ''} detected from SEC filings.`;
      }

      // How many transitions
      if (lowerQuery.includes('how many') && lowerQuery.includes('transition')) {
        return `${company.name} has had **${company.transitionCount}** CEO transition${company.transitionCount !== 1 ? 's' : ''} detected in our dataset.`;
      }

      // Data source questions
      if (lowerQuery.includes('data') || lowerQuery.includes('source') || lowerQuery.includes('where')) {
        return "CEO transitions are detected from **SEC 10-K annual filings** (EDGAR database). Stock data is daily adjusted close prices from **Yahoo Finance**, spanning 1996-2025.";
      }

      // Catch-all for analysis view
      return `I can tell you about **${transition.newCEO}** (new CEO), **${transition.previousCEO}** (previous CEO), stock impact, price, volatility, transition date, or company details. What would you like to know?`;
    }

    return "I'm not sure about that. Try asking about the CEO, stock impact, volatility, or company details.";
  };

  const handleSendMessage = (e?: React.FormEvent) => {
    e?.preventDefault();

    if (!inputValue.trim()) return;

    const newUserMessage: Message = {
      id: Date.now().toString(),
      text: inputValue,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, newUserMessage]);
    setInputValue('');
    setIsTyping(true);

    setTimeout(() => {
      const responseText = generateResponse(newUserMessage.text);
      const newBotMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: responseText,
        sender: 'bot',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, newBotMessage]);
      setIsTyping(false);
    }, 800);
  };

  return (
    <>
      {/* Toggle Button */}
      <motion.button
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 bg-slate-900 text-white rounded-full shadow-xl flex items-center justify-center border-2 border-slate-700 hover:bg-slate-800 transition-colors"
      >
        {isOpen ? <X className="w-6 h-6" /> : <Bot className="w-7 h-7" />}
      </motion.button>

      {/* Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="fixed bottom-24 right-6 z-50 w-full max-w-sm bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col h-[500px]"
          >
            {/* Header */}
            <div className="bg-slate-900 p-4 text-white flex items-center gap-3 shadow-sm">
              <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <div>
                <h3 className="font-bold text-sm">Analyst AI</h3>
                <p className="text-xs text-slate-400 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                  Online
                </p>
              </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] p-3 rounded-2xl text-sm leading-relaxed shadow-sm ${
                      msg.sender === 'user'
                        ? 'bg-slate-900 text-white rounded-tr-none'
                        : 'bg-white text-slate-700 border border-slate-200 rounded-tl-none'
                    }`}
                  >
                     <div dangerouslySetInnerHTML={{ __html: msg.text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
                     <div className={`text-[10px] mt-1 ${msg.sender === 'user' ? 'text-slate-400' : 'text-slate-400'}`}>
                       {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                     </div>
                  </div>
                </div>
              ))}

              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-white border border-slate-200 p-4 rounded-2xl rounded-tl-none shadow-sm flex gap-1 items-center">
                    <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                    <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                    <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 bg-white border-t border-slate-100">
              {currentView === 'analysis' && company && transition && messages.length < 3 && (
                <div className="flex gap-2 overflow-x-auto pb-3 mb-1 no-scrollbar">
                  <button
                    onClick={() => { setInputValue("Who is the new CEO?"); }}
                    className="flex-shrink-0 text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-full transition-colors"
                  >
                    Who is the CEO?
                  </button>
                  <button
                    onClick={() => { setInputValue("What was the stock impact?"); }}
                    className="flex-shrink-0 text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-full transition-colors"
                  >
                    Stock Impact?
                  </button>
                  <button
                    onClick={() => { setInputValue("What is the volatility risk?"); }}
                    className="flex-shrink-0 text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-full transition-colors"
                  >
                    Volatility?
                  </button>
                </div>
              )}

              <form onSubmit={handleSendMessage} className="flex gap-2">
                <input
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Ask a question..."
                  className="flex-1 bg-slate-50 border-transparent focus:border-slate-300 focus:bg-white rounded-lg px-4 py-2 text-sm outline-none transition-all"
                />
                <Button
                  type="submit"
                  size="icon"
                  className="bg-slate-900 hover:bg-slate-800 text-white rounded-lg w-10 h-10 flex-shrink-0"
                  disabled={!inputValue.trim() || isTyping}
                >
                  <Send className="w-4 h-4" />
                </Button>
              </form>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
