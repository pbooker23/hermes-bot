/**
 * HUSTLE FREQUENCY — Evolution Engine
 * 5 videos/day + AI learning system
 * Tracks what works, evolves strategy automatically
 * Drops in to /opt/youtube-agent/
 */

const cron = require('node-cron');
const fs = require('fs');
const path = require('path');

const EVOLUTION_FILE = path.join(__dirname, 'data', 'evolution.json');
const PERFORMANCE_FILE = path.join(__dirname, 'data', 'performance.json');

// ── 5 video slots per day (spread for algorithm favor) ────────────────────
const VIDEO_SCHEDULE = [
  { time: '0 6 * * *',  slot: 1, label: '6:00 AM  — Morning Commute' },
  { time: '0 9 * * *',  slot: 2, label: '9:00 AM  — Work Start' },
  { time: '0 12 * * *', slot: 3, label: '12:00 PM — Lunch Break' },
  { time: '0 17 * * *', slot: 4, label: '5:00 PM  — After Work' },
  { time: '0 20 * * *', slot: 5, label: '8:00 PM  — Prime Time' },
];

// ── Content formats that rotate & evolve ─────────────────────────────────
const CONTENT_FORMATS = [
  { id: 'listicle',    name: 'Top X List',         hook: 'Top {N} ways to...',         weight: 1.0 },
  { id: 'howto',       name: 'How To Tutorial',     hook: 'How I made ${X} with...',    weight: 1.0 },
  { id: 'mistake',     name: 'Mistakes to Avoid',   hook: '{N} mistakes costing you...', weight: 1.0 },
  { id: 'secret',      name: 'Hidden Secret',       hook: 'Nobody talks about this...', weight: 1.0 },
  { id: 'challenge',   name: '24hr/7day Challenge', hook: 'I tried X for {N} days...', weight: 1.0 },
  { id: 'comparison',  name: 'vs Comparison',       hook: 'X vs Y — which pays more?',  weight: 1.0 },
  { id: 'beginner',    name: 'Beginner Guide',      hook: 'Start making money with X (for beginners)', weight: 1.0 },
  { id: 'casestudy',   name: 'Case Study',          hook: 'How this person made ${X}...', weight: 1.0 },
];

// ── Topic pool for Hustle Frequency niche ────────────────────────────────
const TOPIC_POOL = [
  'passive income', 'side hustles', 'make money online', 'financial freedom',
  'affiliate marketing', 'dropshipping', 'print on demand', 'Etsy shop',
  'YouTube automation', 'faceless YouTube', 'digital products', 'PLR ebooks',
  'freelancing', 'fiverr gigs', 'upwork tips', 'AI tools to make money',
  'government contracts small business', 'Amazon FBA', 'Gumroad selling',
  'Canva templates selling', 'social media manager', 'email marketing',
  'cash app flips', 'credit card rewards', 'real estate wholesaling',
  'vending machines', 'laundromat business', 'car flipping', 'domain flipping',
  'stock photography', 'sell feet pics', 'voice over work', 'transcription jobs',
  'survey sites that pay', 'cashback apps', 'reselling thrift stores',
];

class EvolutionEngine {
  constructor() {
    this.data = this.loadEvolutionData();
    this.performance = this.loadPerformanceData();
  }

  loadEvolutionData() {
    try {
      if (fs.existsSync(EVOLUTION_FILE)) {
        return JSON.parse(fs.readFileSync(EVOLUTION_FILE, 'utf8'));
      }
    } catch (e) {}
    return {
      generation: 1,
      totalVideos: 0,
      formatWeights: {},
      topicWeights: {},
      bestHours: [6, 9, 12, 17, 20],
      winningFormulas: [],
      avoidList: [],
      lastEvolution: null,
      weeklyInsights: []
    };
  }

  loadPerformanceData() {
    try {
      if (fs.existsSync(PERFORMANCE_FILE)) {
        return JSON.parse(fs.readFileSync(PERFORMANCE_FILE, 'utf8'));
      }
    } catch (e) {}
    return { videos: [] };
  }

  save() {
    fs.mkdirSync(path.dirname(EVOLUTION_FILE), { recursive: true });
    fs.writeFileSync(EVOLUTION_FILE, JSON.stringify(this.data, null, 2));
    fs.writeFileSync(PERFORMANCE_FILE, JSON.stringify(this.performance, null, 2));
  }

  // ── Pick the best format based on learned weights ──────────────────────
  pickFormat() {
    const formats = CONTENT_FORMATS.map(f => ({
      ...f,
      weight: this.data.formatWeights[f.id] || f.weight
    }));
    const totalWeight = formats.reduce((sum, f) => sum + f.weight, 0);
    let rand = Math.random() * totalWeight;
    for (const format of formats) {
      rand -= format.weight;
      if (rand <= 0) return format;
    }
    return formats[0];
  }

  // ── Pick the best topic based on learned weights ───────────────────────
  pickTopic() {
    const topics = TOPIC_POOL
      .filter(t => !this.data.avoidList.includes(t))
      .map(t => ({
        topic: t,
        weight: this.data.topicWeights[t] || 1.0
      }));
    const totalWeight = topics.reduce((sum, t) => sum + t.weight, 0);
    let rand = Math.random() * totalWeight;
    for (const t of topics) {
      rand -= t.weight;
      if (rand <= 0) return t.topic;
    }
    return topics[Math.floor(Math.random() * topics.length)].topic;
  }

  // ── Record video performance and evolve weights ────────────────────────
  recordPerformance(videoId, title, format, topic, metrics) {
    const score = this.calculateScore(metrics);

    this.performance.videos.push({
      videoId, title, format, topic, metrics, score,
      recordedAt: new Date().toISOString()
    });

    // Evolve format weight
    const currentFormatWeight = this.data.formatWeights[format] || 1.0;
    if (score > 70) {
      this.data.formatWeights[format] = Math.min(3.0, currentFormatWeight * 1.15);
    } else if (score < 30) {
      this.data.formatWeights[format] = Math.max(0.2, currentFormatWeight * 0.85);
    }

    // Evolve topic weight
    const currentTopicWeight = this.data.topicWeights[topic] || 1.0;
    if (score > 70) {
      this.data.topicWeights[topic] = Math.min(3.0, currentTopicWeight * 1.2);
      if (score > 90 && !this.data.winningFormulas.find(w => w.topic === topic)) {
        this.data.winningFormulas.push({ topic, format, score, title });
      }
    } else if (score < 20) {
      this.data.topicWeights[topic] = Math.max(0.1, currentTopicWeight * 0.7);
      if (score < 10) {
        this.data.avoidList.push(topic);
      }
    }

    this.data.totalVideos++;
    this.save();
    return score;
  }

  calculateScore(metrics) {
    const { views = 0, watchTime = 0, ctr = 0, likes = 0, comments = 0, subscribers = 0 } = metrics;
    return Math.min(100, Math.round(
      (Math.min(views / 1000, 30)) +       // up to 30 pts — views
      (Math.min(watchTime / 5, 20)) +      // up to 20 pts — watch time %
      (Math.min(ctr * 100, 20)) +          // up to 20 pts — CTR
      (Math.min(likes / 10, 15)) +         // up to 15 pts — likes
      (Math.min(comments / 5, 10)) +       // up to 10 pts — comments
      (Math.min(subscribers, 5))           // up to  5 pts — new subs
    ));
  }

  // ── Weekly evolution — analyze and update strategy ────────────────────
  weeklyEvolution() {
    const recentVideos = this.performance.videos.slice(-35); // last 35 = ~7 days
    if (recentVideos.length < 5) return;

    const avgScore = recentVideos.reduce((s, v) => s + v.score, 0) / recentVideos.length;
    const topVideos = [...recentVideos].sort((a, b) => b.score - a.score).slice(0, 5);
    const bottomVideos = [...recentVideos].sort((a, b) => a.score - b.score).slice(0, 5);

    const insight = {
      generation: this.data.generation,
      week: new Date().toISOString().split('T')[0],
      avgScore: Math.round(avgScore),
      topFormats: topVideos.map(v => v.format),
      topTopics: topVideos.map(v => v.topic),
      weakFormats: bottomVideos.map(v => v.format),
      weakTopics: bottomVideos.map(v => v.topic),
      winningFormulas: this.data.winningFormulas.slice(-5),
      totalVideos: this.data.totalVideos
    };

    this.data.weeklyInsights.push(insight);
    this.data.generation++;
    this.data.lastEvolution = new Date().toISOString();
    this.save();

    console.log(`\n🧬 EVOLUTION GEN ${insight.generation - 1} COMPLETE`);
    console.log(`📊 Avg score: ${insight.avgScore}/100`);
    console.log(`🏆 Top topics: ${[...new Set(insight.topTopics)].join(', ')}`);
    console.log(`📉 Weak topics: ${[...new Set(insight.weakTopics)].join(', ')}`);

    return insight;
  }

  getStatus() {
    const topFormats = Object.entries(this.data.formatWeights)
      .sort(([,a],[,b]) => b - a).slice(0, 3)
      .map(([id, w]) => `${id}(${w.toFixed(2)})`);
    const topTopics = Object.entries(this.data.topicWeights)
      .sort(([,a],[,b]) => b - a).slice(0, 5)
      .map(([t, w]) => `${t}(${w.toFixed(2)})`);

    return {
      generation: this.data.generation,
      totalVideos: this.data.totalVideos,
      topFormats,
      topTopics,
      winningFormulas: this.data.winningFormulas.length,
      avoidList: this.data.avoidList.length,
      lastEvolution: this.data.lastEvolution
    };
  }
}

// ── Scheduler — 5 videos/day ─────────────────────────────────────────────
class HustleFrequencyScheduler {
  constructor(agents, database) {
    this.agents = agents;
    this.db = database;
    this.engine = new EvolutionEngine();
    this.tasks = new Map();
  }

  async initialize() {
    console.log('🎬 HUSTLE FREQUENCY — Evolution Engine Starting');
    console.log(`📊 Generation: ${this.engine.data.generation}`);
    console.log(`🎥 Total videos produced: ${this.engine.data.totalVideos}`);
    console.log(`⏰ Schedule: 5 videos/day at 6AM, 9AM, 12PM, 5PM, 8PM\n`);

    // Schedule 5 daily video slots
    VIDEO_SCHEDULE.forEach(({ time, slot, label }) => {
      const task = cron.schedule(time, async () => {
        await this.generateVideo(slot, label);
      });
      this.tasks.set(`video-slot-${slot}`, task);
      console.log(`✅ Scheduled: ${label}`);
    });

    // Analytics collection — 10 AM daily
    cron.schedule('0 10 * * *', () => this.collectAnalytics());

    // Evolution — Sunday midnight
    cron.schedule('0 0 * * 0', () => this.engine.weeklyEvolution());

    // Nightly optimization — 11 PM
    cron.schedule('0 23 * * *', () => this.optimizeStrategy());

    console.log('\n🧬 Evolution engine active — learning from every video\n');
  }

  async generateVideo(slot, label) {
    try {
      console.log(`\n🎬 [SLOT ${slot}] ${label} — Generating video...`);

      const format = this.engine.pickFormat();
      const topic = this.engine.pickTopic();

      console.log(`📝 Format: ${format.name} | Topic: ${topic}`);

      // Generate content using existing agents
      const strategy = await this.agents.strategy.generateContentStrategy({
        topic,
        format: format.name,
        hook: format.hook,
        niche: 'money, side hustles, passive income, financial freedom',
        audience: 'people looking for ways to make money online'
      });

      const script = await this.agents.scriptWriter.generateScript(strategy);
      const thumbnail = await this.agents.thumbnailDesigner.generateThumbnail(script);
      const seoData = await this.agents.seoOptimizer.optimize(script, strategy);

      const productionData = await this.agents.production.processContent({
        strategy, script, thumbnail, seo: seoData,
        metadata: { format: format.id, topic, slot, evolutionGen: this.engine.data.generation }
      });

      await this.agents.publishing.scheduleContent(productionData);

      // Log to evolution engine
      await this.db.executeQuery(
        `INSERT INTO automation_events (event_type, status, data, created_at) 
         VALUES (?, ?, ?, datetime('now'))`,
        ['video_generated', 'success', JSON.stringify({
          slot, format: format.id, topic,
          title: script.title,
          generation: this.engine.data.generation
        })]
      );

      console.log(`✅ [SLOT ${slot}] Done: "${script.title}"`);

    } catch (error) {
      console.error(`❌ [SLOT ${slot}] Failed: ${error.message}`);
    }
  }

  async collectAnalytics() {
    try {
      console.log('\n📊 Collecting analytics...');
      const recentVideos = await this.db.getAllRows(
        `SELECT * FROM publish_schedule WHERE status='published' 
         AND published_at > datetime('now', '-7 days')`
      );

      for (const video of recentVideos) {
        try {
          const analytics = await this.agents.analytics.analyzeVideoPerformance(video.youtube_id);
          if (analytics && video.metadata) {
            const meta = JSON.parse(video.metadata || '{}');
            if (meta.format && meta.topic) {
              const score = this.engine.recordPerformance(
                video.youtube_id, video.title,
                meta.format, meta.topic,
                {
                  views: analytics.statistics?.viewCount || 0,
                  watchTime: analytics.watchTimePercentage || 0,
                  ctr: analytics.clickThroughRate || 0,
                  likes: analytics.statistics?.likeCount || 0,
                  comments: analytics.statistics?.commentCount || 0,
                  subscribers: analytics.subscribersGained || 0
                }
              );
              console.log(`📈 "${video.title}" — Score: ${score}/100`);
            }
          }
          await new Promise(r => setTimeout(r, 1000));
        } catch (e) {
          console.error(`Analytics error for ${video.youtube_id}: ${e.message}`);
        }
      }
    } catch (error) {
      console.error('Analytics collection failed:', error.message);
    }
  }

  async optimizeStrategy() {
    const status = this.engine.getStatus();
    console.log('\n🧬 NIGHTLY OPTIMIZATION');
    console.log(`Generation: ${status.generation} | Videos: ${status.totalVideos}`);
    console.log(`Top formats: ${status.topFormats.join(', ')}`);
    console.log(`Top topics: ${status.topTopics.join(', ')}`);
    console.log(`Winning formulas: ${status.winningFormulas}`);
    console.log(`Avoid list: ${status.avoidList} topics\n`);
  }
}

module.exports = { HustleFrequencyScheduler, EvolutionEngine };
