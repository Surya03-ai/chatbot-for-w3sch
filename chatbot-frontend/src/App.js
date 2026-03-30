import Chatbot from './Chatbot';
import './index.css';

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white p-8">
      <div className="max-w-6xl mx-auto py-20">
        <div className="text-center mb-20">
          <h1 className="text-6xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent mb-6">
            Learn Web Development
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
            Master HTML, CSS, JavaScript and more with our step-by-step tutorials. 
            Use the W3Guide AI assistant (bottom-right) for instant help!
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {[
            { title: 'HTML Tutorial', desc: 'Learn HTML from scratch with examples', color: 'from-blue-500 to-blue-600' },
            { title: 'CSS Tutorial', desc: 'Master CSS styling, layouts and animations', color: 'from-emerald-500 to-emerald-600' },
            { title: 'JavaScript', desc: 'JavaScript for beginners to advanced', color: 'from-purple-500 to-purple-600' },
            { title: 'Python', desc: 'Python programming tutorial', color: 'from-orange-500 to-orange-600' },
            { title: 'SQL', desc: 'Database tutorial with SQL queries', color: 'from-indigo-500 to-indigo-600' },
            { title: 'React', desc: 'Modern React development tutorial', color: 'from-pink-500 to-pink-600' }
          ].map((card, i) => (
            <div key={i} className="group cursor-pointer">
              <div className="h-64 bg-white border border-gray-200 rounded-3xl p-8 hover:shadow-2xl hover:-translate-y-2 transition-all duration-300 hover:border-gray-300">
                <h3 className={`text-2xl font-bold bg-gradient-to-r ${card.color} bg-clip-text text-transparent mb-4`}>
                  {card.title}
                </h3>
                <p className="text-gray-600 leading-relaxed">{card.desc}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-32 text-center">
          <p className="text-lg text-gray-500">
            Scroll down to see more content. Notice how the W3Guide AI stays fixed at bottom-right! 👇
          </p>
        </div>

        {/* Long scrollable content */}
        <div className="mt-32 space-y-12">
          {Array.from({ length: 20 }).map((_, i) => (
            <div key={i} className="h-48 bg-gradient-to-r from-gray-50 to-gray-100 rounded-2xl p-12 border border-gray-200">
              <h3 className="text-3xl font-bold text-gray-800 mb-4">Tutorial Section {i + 1}</h3>
              <p className="text-xl text-gray-600 leading-relaxed">
                This demonstrates the chatbot stays perfectly positioned while scrolling. Perfect for educational websites!
              </p>
            </div>
          ))}
        </div>
      </div>
      <Chatbot />
    </div>
  );
}

export default App;

