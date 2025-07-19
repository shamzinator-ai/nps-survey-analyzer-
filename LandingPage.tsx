import { motion } from 'framer-motion';

export default function LandingPage() {
  return (
    <div className="font-sans text-gray-800">
      {/* Hero Section */}
      <section className="max-w-[1200px] mx-auto px-4 py-[72px] text-center space-y-6">
        <h1 className="text-4xl md:text-6xl font-semibold">
          <span aria-hidden="true">⚡</span> Radar spots the stories that spike your growth
        </h1>
        <p className="text-lg md:text-2xl text-gray-600">
          We scan world news 24-7 and turn fresh headlines into instant action plans. Less scrolling, more winning.
        </p>
        <div className="flex justify-center gap-4 pt-4">
          <button aria-label="Get Started Free" className="bg-indigo-500 hover:bg-indigo-600 text-white font-medium py-3 px-6 rounded-full transition-colors">
            Get Started Free
          </button>
          <button aria-label="Watch Demo" className="border border-indigo-500 text-indigo-500 hover:bg-indigo-50 font-medium py-3 px-6 rounded-full transition-colors">
            Watch Demo
          </button>
        </div>
      </section>

      {/* Value Pillars Grid */}
      <section className="max-w-[1200px] mx-auto px-4 py-12 grid gap-8 grid-cols-1 sm:grid-cols-2 md:grid-cols-3">
        {[
          ['\uD83D\uDCF0', 'See It First', 'Real-time feed shows breaking edu-news the moment it drops \u2013 ranked by relevance to you.'],
          ['\uD83E\uDD14', 'Know Every Rival', 'AI auto-tracks emerging competitors so you can outpace them before they trend.'],
          ['\uD83D\uDD17', 'Backlinks, Not Busywork', 'We find guest-post sites for you \u2013 tap once and pitch.'],
          ['\uD83D\uDCE3', 'PR in One Click', 'Pull a journo\u2019s email and fire a tailored pitch faster than they can tweet.'],
          ['\u2728', 'Ideas On-Demand', 'No more blank pages \u2013 Radar suggests hot takes your audience actually cares about.'],
          ['\uD83D\uDCBC', 'Deals in Sight', 'Spot acquisition targets early with funding, staff count, and traction intel all in one card.'],
        ].map(([icon, title, text]) => (
          <motion.div
            key={title}
            className="bg-white/60 backdrop-blur p-6 rounded-lg shadow-sm" 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4 }}
          >
            <div className="flex items-start gap-3">
              <span aria-hidden="true" className="text-2xl">{icon}</span>
              <h3 className="font-semibold text-xl">{title}</h3>
            </div>
            <p className="mt-2 text-gray-600 text-sm leading-relaxed">{text}</p>
          </motion.div>
        ))}
      </section>

      {/* Social Proof Strip */}
      <section className="bg-gray-50 py-8">
        <div className="max-w-[1200px] mx-auto px-4 text-center">
          <p className="font-medium">Trusted by 30+ edu-startups & 4,000 marketers</p>
          <div className="flex items-center justify-center gap-8 mt-4 animate-pulse">
            <div className="h-8 w-24 bg-gray-200 rounded" />
            <div className="h-8 w-24 bg-gray-200 rounded" />
            <div className="h-8 w-24 bg-gray-200 rounded" />
            <div className="h-8 w-24 bg-gray-200 rounded" />
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="max-w-[1200px] mx-auto px-4 py-12 grid gap-8 sm:grid-cols-3 text-center">
        {[
          ['1\uFE0F\u20E3', 'Plug in your keywords'],
          ['2\uFE0F\u20E3', 'Radar reads the world for you'],
          ['3\uFE0F\u20E3', 'You act before anyone else'],
        ].map(([icon, text]) => (
          <motion.div
            key={text}
            className="space-y-2"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.2 }}
          >
            <span aria-hidden="true" className="text-3xl">{icon}</span>
            <p className="font-medium">{text}</p>
          </motion.div>
        ))}
      </section>

      {/* CTA Banner */}
      <section className="text-center py-12 bg-gradient-to-r from-indigo-50 to-purple-50">
        <h2 className="text-2xl md:text-3xl font-semibold mb-4">Ready to move faster than the headlines?</h2>
        <button
          aria-label="Try Radar Now"
          className="bg-indigo-500 hover:bg-indigo-600 text-white font-medium py-3 px-8 rounded-full transition-all animate-pulse hover:animate-none"
        >
          Try Radar Now
        </button>
      </section>

      {/* Footer */}
      <footer className="text-center py-6 text-sm text-gray-500">
        <nav className="space-x-4">
          <a href="#" className="hover:text-gray-700">Product</a>
          <a href="#" className="hover:text-gray-700">Pricing</a>
          <a href="#" className="hover:text-gray-700">Careers</a>
          <a href="#" className="hover:text-gray-700">Privacy</a>
        </nav>
        <p className="mt-2">Built with <span aria-hidden="true">☕</span> in Sheffield, UK</p>
      </footer>
    </div>
  );
}

