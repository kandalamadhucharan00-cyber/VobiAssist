import { useEffect, useMemo, useRef, useState } from 'react';
import { Activity, Bot, CheckCircle2, CircleDashed, Download, MessageSquare, Mic, PhoneCall, ServerCog, ShieldCheck, Sparkles, Volume2, Wand2 } from 'lucide-react';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

type NavKey = 'overview' | 'assistant' | 'explorer' | 'monitor' | 'webhooks' | 'troubleshooting' | 'settings';

type MetricCard = { title: string; value: string; subtitle: string; tone: 'cyan' | 'emerald' | 'amber' | 'rose' };

type ChatMessage = { id: number; role: 'user' | 'assistant'; text: string };

const backendUrl = 'http://localhost:8000';

const chartData = [
  { name: 'Mon', calls: 12 },
  { name: 'Tue', calls: 19 },
  { name: 'Wed', calls: 15 },
  { name: 'Thu', calls: 22 },
  { name: 'Fri', calls: 17 },
  { name: 'Sat', calls: 27 },
  { name: 'Sun', calls: 20 },
];

const navItems: { key: NavKey; label: string }[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'assistant', label: 'AI Voice Assistant' },
  { key: 'explorer', label: 'Vobiz API Explorer' },
  { key: 'monitor', label: 'Call Monitor' },
  { key: 'webhooks', label: 'Webhook Lab' },
  { key: 'troubleshooting', label: 'Troubleshooting Center' },
  { key: 'settings', label: 'Settings' },
];

function App() {
  const [activeTab, setActiveTab] = useState<NavKey>('overview');
  const [health, setHealth] = useState<any>(null);
  const [config, setConfig] = useState<any>(null);
  const [chatInput, setChatInput] = useState('How do I troubleshoot a 401 error?');
  const [messages, setMessages] = useState<ChatMessage[]>([
    { id: 1, role: 'assistant', text: 'I can help with Vobiz auth, SIP/RTP, webhook duplicate handling, and bad outbound call setup.' },
  ]);
  const [isListening, setIsListening] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState('Microphone access is available when you click the mic button.');
  const recognitionRef = useRef<any>(null);

  const [connectivity, setConnectivity] = useState<any>(null);
  const [calls, setCalls] = useState<any[]>([]);
  const [webhookStatus, setWebhookStatus] = useState<any>(null);
  const [troubleshootingQuery, setTroubleshootingQuery] = useState('429');
  const [troubleshootingResults, setTroubleshootingResults] = useState<any[]>([]);

  useEffect(() => {
    void loadHealth();
    void loadConfig();
    void loadCalls();
    void loadTroubleshooting();
  }, []);

  const metrics = useMemo<MetricCard[]>(() => [
    { title: 'Connection', value: health ? 'Connected' : 'Not Configured', subtitle: 'Vobiz credentials', tone: health ? 'emerald' : 'amber' },
    { title: 'Recorded Events', value: '42', subtitle: 'Local test events', tone: 'cyan' },
    { title: 'Successful', value: '31', subtitle: 'Valid requests', tone: 'emerald' },
    { title: 'Failed', value: '11', subtitle: 'Errors observed', tone: 'rose' },
  ], [health]);

  const loadHealth = async () => {
    const response = await fetch(`${backendUrl}/api/health`);
    const payload = await response.json();
    setHealth(payload);
  };

  const loadConfig = async () => {
    const response = await fetch(`${backendUrl}/api/config`);
    const payload = await response.json();
    setConfig(payload);
  };

  const loadCalls = async () => {
    const response = await fetch(`${backendUrl}/api/calls?limit=6`);
    const payload = await response.json();
    setCalls(payload);
  };

  const loadTroubleshooting = async () => {
    const params = new URLSearchParams();
    if (troubleshootingQuery) params.set('query', troubleshootingQuery);
    const response = await fetch(`${backendUrl}/api/troubleshooting?${params.toString()}`);
    const payload = await response.json();
    setTroubleshootingResults(payload.items ?? []);
  };

  useEffect(() => {
    void loadTroubleshooting();
  }, [troubleshootingQuery]);

  const sendChat = async () => {
    const trimmed = chatInput.trim();
    if (!trimmed) return;
    setMessages((prev) => [...prev, { id: Date.now(), role: 'user', text: trimmed }]);
    setChatInput('');

    const response = await fetch(`${backendUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: trimmed }),
    });
    const payload = await response.json();
    setMessages((prev) => [...prev, { id: Date.now() + 1, role: 'assistant', text: payload.response }]);

    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(payload.response);
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utterance);
    }
  };

  const startVoiceCapture = async () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const isSecureContext = window.isSecureContext || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

    if (!isSecureContext) {
      setVoiceStatus('Microphone input requires a secure context. Use localhost or HTTPS for voice support.');
      return;
    }

    if (!SpeechRecognition) {
      setVoiceStatus('Speech recognition is not supported in this browser. You can still use text chat.');
      return;
    }

    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        await navigator.mediaDevices.getUserMedia({ audio: true });
      }

      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'en-US';
      recognition.onstart = () => setIsListening(true);
      recognition.onresult = (event: any) => {
        const transcript = Array.from(event.results)
          .map((result: any) => result[0]?.transcript ?? '')
          .join(' ')
          .trim();
        if (transcript) {
          setChatInput(transcript);
          setVoiceStatus(`Transcript captured: “${transcript}”`);
        }
      };
      recognition.onerror = (event: any) => {
        const errorMessage = event?.error || 'unknown';
        setVoiceStatus(`Voice input was unavailable (${errorMessage}). Please allow microphone access or use text input.`);
        setIsListening(false);
      };
      recognition.onend = () => setIsListening(false);
      recognitionRef.current = recognition;
      recognition.start();
    } catch (error: any) {
      setIsListening(false);
      setVoiceStatus('Microphone access was blocked or unavailable. Please allow the browser microphone permission and try again, or use text input instead.');
    }
  };

  const stopVoiceCapture = () => {
    recognitionRef.current?.stop();
    setIsListening(false);
  };

  const testConnection = async () => {
    const response = await fetch(`${backendUrl}/api/vobiz/test-connection`);
    const payload = await response.json();
    setConnectivity(payload);
  };

  const simulateWebhook = async () => {
    const response = await fetch(`${backendUrl}/api/webhooks/simulate`, { method: 'POST' });
    const payload = await response.json();
    setWebhookStatus(payload);
  };

  const toneClasses = {
    cyan: 'border-cyan-500/40 bg-cyan-500/10 text-cyan-300',
    emerald: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300',
    amber: 'border-amber-500/40 bg-amber-500/10 text-amber-300',
    rose: 'border-rose-500/40 bg-rose-500/10 text-rose-300',
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-7xl p-4 md:p-6">
        <header className="mb-6 flex flex-col gap-4 rounded-2xl border border-slate-700 bg-slate-900/80 p-4 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-cyan-500/15 p-2 text-cyan-300"><Bot size={20} /></div>
              <div>
                <div className="text-xs uppercase tracking-[0.18em] text-cyan-300">VobiAssist</div>
                <h1 className="text-2xl font-bold">AI-Powered Voice API Support</h1>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-300">
            <ShieldCheck className="text-emerald-400" size={16} />
            Local demo mode • credentials kept on backend
          </div>
        </header>

        <nav className="mb-6 flex flex-wrap gap-2">
          {navItems.map((item) => (
            <button
              key={item.key}
              onClick={() => setActiveTab(item.key)}
              className={`rounded-full border px-3 py-2 text-sm transition ${activeTab === item.key ? 'border-cyan-400 bg-cyan-500/10 text-cyan-300' : 'border-slate-700 bg-slate-900 text-slate-300 hover:border-slate-500'}`}
            >
              {item.label}
            </button>
          ))}
        </nav>

        {activeTab === 'overview' && (
          <div className="space-y-6">
            <section className="grid gap-4 md:grid-cols-4">
              {metrics.map((metric) => (
                <div key={metric.title} className={`card border ${toneClasses[metric.tone]}`}>
                  <div className="panel-heading">{metric.title}</div>
                  <div className="mt-3 text-3xl font-bold">{metric.value}</div>
                  <div className="mt-1 text-sm opacity-80">{metric.subtitle}</div>
                </div>
              ))}
            </section>

            <section className="grid gap-6 lg:grid-cols-[1.3fr_0.7fr]">
              <div className="card">
                <div className="panel-heading mb-4">Recent call activity</div>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient id="calls" x1="0" x2="0" y1="0" y2="1">
                          <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.7} />
                          <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.05} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid stroke="#334155" strokeDasharray="3 3" />
                      <XAxis dataKey="name" stroke="#94a3b8" />
                      <YAxis stroke="#94a3b8" />
                      <Tooltip />
                      <Area type="monotone" dataKey="calls" stroke="#38bdf8" fill="url(#calls)" strokeWidth={3} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="card">
                <div className="panel-heading mb-4">Quick actions</div>
                <div className="space-y-3">
                  <button onClick={testConnection} className="flex w-full items-center justify-between rounded-xl border border-slate-700 bg-slate-800 px-3 py-3 text-left hover:border-cyan-400">
                    <span>Test connectivity</span>
                    <ServerCog size={18} />
                  </button>
                  <button onClick={() => setActiveTab('assistant')} className="flex w-full items-center justify-between rounded-xl border border-slate-700 bg-slate-800 px-3 py-3 text-left hover:border-cyan-400">
                    <span>Open voice assistant</span>
                    <MessageSquare size={18} />
                  </button>
                  <button onClick={() => setActiveTab('monitor')} className="flex w-full items-center justify-between rounded-xl border border-slate-700 bg-slate-800 px-3 py-3 text-left hover:border-cyan-400">
                    <span>Inspect logs</span>
                    <Download size={18} />
                  </button>
                </div>
              </div>
            </section>
          </div>
        )}

        {activeTab === 'assistant' && (
          <div className="card">
            <div className="panel-heading mb-4">AI Voice Assistant</div>
            <div className="mb-4 flex flex-wrap gap-2">
              <button onClick={() => setChatInput('How do I troubleshoot 401 errors?')} className="rounded-full bg-slate-800 px-3 py-2 text-sm hover:bg-slate-700">401 example</button>
              <button onClick={() => setChatInput('Why is my outbound call failing?')} className="rounded-full bg-slate-800 px-3 py-2 text-sm hover:bg-slate-700">Outbound call</button>
              <button onClick={() => setChatInput('My call connects but there is no audio.')} className="rounded-full bg-slate-800 px-3 py-2 text-sm hover:bg-slate-700">No audio</button>
            </div>

            <div className="mb-4 space-y-3 rounded-2xl border border-slate-700 bg-slate-950/60 p-4">
              {messages.map((message) => (
                <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[75%] rounded-2xl px-3 py-2 ${message.role === 'user' ? 'bg-cyan-500/20 text-cyan-100' : 'bg-slate-800 text-slate-100'}`}>
                    {message.text}
                  </div>
                </div>
              ))}
            </div>

            <div className="flex flex-col gap-3 md:flex-row">
              <textarea value={chatInput} onChange={(e) => setChatInput(e.target.value)} rows={3} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-3 text-slate-100 outline-none focus:border-cyan-400" placeholder="Ask about Vobiz auth, SIP, RTP, or webhook issues..." />
            </div>

            <div className="mt-4 flex flex-wrap gap-3">
              <button onClick={sendChat} className="rounded-xl bg-cyan-500 px-4 py-3 font-medium text-slate-950 hover:bg-cyan-400">Send</button>
              <button onClick={isListening ? stopVoiceCapture : startVoiceCapture} className="flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 hover:border-cyan-400">
                <Mic size={16} /> {isListening ? 'Stop listening' : 'Use microphone'}
              </button>
              <button onClick={() => setMessages([{ id: Date.now(), role: 'assistant', text: 'Conversation reset. Ask a Vobiz troubleshooting question.' }])} className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 hover:border-cyan-400">Reset</button>
              <button onClick={() => window.speechSynthesis?.cancel()} className="flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 hover:border-cyan-400"><Volume2 size={16} /> Stop speech</button>
            </div>

            <div className="mt-3 text-sm text-slate-300">{voiceStatus}</div>
          </div>
        )}

        {activeTab === 'explorer' && (
          <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="card">
              <div className="panel-heading mb-4">Vobiz API Explorer</div>
              <button onClick={testConnection} className="mb-4 rounded-xl bg-cyan-500 px-4 py-3 font-medium text-slate-950 hover:bg-cyan-400">Run connectivity test</button>
              {connectivity && (
                <div className="space-y-3 rounded-2xl border border-slate-700 bg-slate-950/60 p-4 text-sm text-slate-200">
                  <div><span className="text-slate-400">Status:</span> {connectivity.ok ? 'Connected' : 'Error'} </div>
                  <div><span className="text-slate-400">Endpoint:</span> {connectivity.endpoint}</div>
                  <div><span className="text-slate-400">HTTP:</span> {connectivity.status_code ?? 'n/a'}</div>
                  <div><span className="text-slate-400">Duration:</span> {connectivity.duration_ms ?? 0} ms</div>
                  <div><span className="text-slate-400">Message:</span> {connectivity.message}</div>
                  {connectivity.response_preview && <pre className="overflow-auto rounded-xl bg-slate-900 p-3 text-xs text-slate-300">{connectivity.response_preview}</pre>}
                </div>
              )}
            </div>

            <div className="card">
              <div className="panel-heading mb-4">Safety checks</div>
              <ul className="space-y-3 text-sm text-slate-300">
                <li className="flex items-center gap-2"><CheckCircle2 className="text-emerald-400" size={16} /> Auth headers are kept server-side</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="text-emerald-400" size={16} /> Real calls remain disabled by default</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="text-emerald-400" size={16} /> The app does not allow arbitrary external URLs</li>
              </ul>
            </div>
          </div>
        )}

        {activeTab === 'monitor' && (
          <div className="card">
            <div className="panel-heading mb-4">Call Monitor</div>
            <div className="grid gap-3 md:grid-cols-3">
              <div className="rounded-xl border border-slate-700 bg-slate-950 p-3"><span className="text-slate-400">Call ID</span><div className="mt-1">call_1041</div></div>
              <div className="rounded-xl border border-slate-700 bg-slate-950 p-3"><span className="text-slate-400">Status</span><div className="mt-1 text-emerald-300">completed</div></div>
              <div className="rounded-xl border border-slate-700 bg-slate-950 p-3"><span className="text-slate-400">Event source</span><div className="mt-1">Simulation</div></div>
            </div>
            <div className="mt-5 space-y-3">
              {calls.map((call) => (
                <div key={call.id} className="flex flex-col gap-2 rounded-xl border border-slate-700 bg-slate-950/60 p-4 md:flex-row md:items-center md:justify-between">
                  <div>
                    <div className="font-medium text-cyan-300">{call.call_id}</div>
                    <div className="text-sm text-slate-400">{call.source_number} → {call.destination_number}</div>
                  </div>
                  <div className="text-sm text-slate-300">{call.status}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'webhooks' && (
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="card">
              <div className="panel-heading mb-4">Webhook Lab</div>
              <button onClick={simulateWebhook} className="rounded-xl bg-cyan-500 px-4 py-3 font-medium text-slate-950 hover:bg-cyan-400">Send simulated webhook</button>
              {webhookStatus && <div className="mt-4 rounded-xl border border-slate-700 bg-slate-950/60 p-4 text-sm text-slate-200">{JSON.stringify(webhookStatus, null, 2)}</div>}
            </div>
            <div className="card">
              <div className="panel-heading mb-4">Duplicate handling</div>
              <div className="rounded-xl border border-dashed border-slate-600 bg-slate-950/60 p-4 text-sm text-slate-300">
                Duplicate events are rejected by checking the event_id in SQLite, so a second delivery does not re-trigger processing.
              </div>
            </div>
          </div>
        )}

        {activeTab === 'troubleshooting' && (
          <div className="card">
            <div className="panel-heading mb-4">Troubleshooting Center</div>
            <div className="mb-4">
              <input value={troubleshootingQuery} onChange={(e) => setTroubleshootingQuery(e.target.value)} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-3 text-slate-100" placeholder="Search 401, 429, webhook, RTP, SIP..." />
            </div>
            <div className="space-y-3">
              {troubleshootingResults.map((item) => (
                <div key={item.id} className="rounded-xl border border-slate-700 bg-slate-950/60 p-4">
                  <div className="mb-1 text-sm text-cyan-300">{item.category}</div>
                  <div className="font-medium">{item.title}</div>
                  <div className="mt-2 text-sm text-slate-300">{item.content}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="card">
              <div className="panel-heading mb-4">System settings</div>
              {config ? (
                <div className="space-y-3 text-sm text-slate-300">
                  <div><span className="text-slate-400">Backend health:</span> {config.health}</div>
                  <div><span className="text-slate-400">Vobiz configured:</span> {config.vobiz_configured ? 'Yes' : 'No'}</div>
                  <div><span className="text-slate-400">AI mode:</span> {config.ai_provider}</div>
                  <div><span className="text-slate-400">App version:</span> {config.version}</div>
                </div>
              ) : <div>Loading settings...</div>}
            </div>
            <div className="card">
              <div className="panel-heading mb-4">Documentation links</div>
              <div className="space-y-3 text-sm text-slate-300">
                <a className="block rounded-xl border border-slate-700 bg-slate-950 p-3 hover:border-cyan-400" href="https://www.vobiz.ai/docs/llms.txt" target="_blank">Vobiz docs index</a>
                <a className="block rounded-xl border border-slate-700 bg-slate-950 p-3 hover:border-cyan-400" href="https://www.vobiz.ai/openapi.json" target="_blank">OpenAPI specification</a>
                <a className="block rounded-xl border border-slate-700 bg-slate-950 p-3 hover:border-cyan-400" href="https://console.vobiz.ai" target="_blank">Developer console</a>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
