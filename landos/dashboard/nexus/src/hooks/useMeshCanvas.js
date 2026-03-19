import { useEffect, useRef, useCallback } from 'react';
import { AGENTS } from '../data/agents';

const FAMILY_COLORS = {
  LISTING: '#00f0ff', CLUSTER: '#a855f7', PARCEL: '#3b82f6',
  MUNICIPAL: '#ffb800', DEV_EXIT: '#ff2d55', OPPORTUNITY: '#00ff88', HISTORICAL: '#f97316',
};

export default function useMeshCanvas(canvasRef) {
  const nodesRef = useRef([]);
  const particlesRef = useRef([]);
  const animRef = useRef(null);

  const initNodes = useCallback((W, H) => {
    const cx = W / 2, cy = H / 2, radius = Math.min(W, H) * 0.32;
    const nodes = AGENTS.map((a, i) => {
      const angle = (i / AGENTS.length) * Math.PI * 2 - Math.PI / 2;
      return { x: cx + Math.cos(angle) * radius, y: cy + Math.sin(angle) * radius, r: 22, color: a.color, icon: a.icon, name: a.name, phase: Math.random() * 6.28, glow: 0 };
    });
    nodes.push({ x: cx, y: cy, r: 34, color: '#c9a44e', icon: '⚡', name: 'Trigger Engine', phase: 0, glow: 0.5 });
    nodesRef.current = nodes;
  }, []);

  const spawnParticle = useCallback((family) => {
    const nodes = nodesRef.current;
    if (nodes.length < 2) return;
    const hub = nodes.length - 1;
    const from = Math.floor(Math.random() * (nodes.length - 1));
    const rev = Math.random() > 0.5;
    const s = rev ? nodes[hub] : nodes[from];
    const e = rev ? nodes[from] : nodes[hub];
    const color = FAMILY_COLORS[family] || '#ffffff30';
    particlesRef.current.push({ sx: s.x, sy: s.y, ex: e.x, ey: e.y, x: s.x, y: s.y, p: 0, spd: 0.008 + Math.random() * 0.012, color, size: 2 + Math.random() * 2, trail: [] });
    nodes[rev ? from : hub].glow = Math.min(nodes[rev ? from : hub].glow + 0.3, 1.5);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let W, H;

    const resize = () => {
      const rect = canvas.parentElement.getBoundingClientRect();
      const dpr = devicePixelRatio || 1;
      W = rect.width; H = rect.height;
      canvas.width = W * dpr; canvas.height = H * dpr;
      canvas.style.width = W + 'px'; canvas.style.height = H + 'px';
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      initNodes(W, H);
    };

    resize();
    window.addEventListener('resize', resize);

    const draw = (t) => {
      ctx.clearRect(0, 0, W, H);
      const nodes = nodesRef.current;
      const particles = particlesRef.current;

      // Grid
      ctx.strokeStyle = 'rgba(255,255,255,0.02)'; ctx.lineWidth = 0.5;
      for (let x = 0; x < W; x += 40) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
      for (let y = 0; y < H; y += 40) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }

      // Connections
      const hub = nodes.length - 1;
      for (let i = 0; i < AGENTS.length; i++) {
        ctx.beginPath(); ctx.moveTo(nodes[i].x, nodes[i].y); ctx.lineTo(nodes[hub].x, nodes[hub].y);
        ctx.strokeStyle = 'rgba(255,255,255,0.035)'; ctx.lineWidth = 1; ctx.setLineDash([4, 8]); ctx.stroke(); ctx.setLineDash([]);
      }

      // Particles
      for (let pi = particles.length - 1; pi >= 0; pi--) {
        const p = particles[pi];
        p.p += p.spd;
        if (p.p >= 1) { particles.splice(pi, 1); continue; }
        const ease = p.p < 0.5 ? 4 * p.p ** 3 : 1 - (-2 * p.p + 2) ** 3 / 2;
        p.x = p.sx + (p.ex - p.sx) * ease;
        p.y = p.sy + (p.ey - p.sy) * ease;
        p.trail.push({ x: p.x, y: p.y }); if (p.trail.length > 12) p.trail.shift();
        const [r, g, b] = [parseInt(p.color.slice(1, 3), 16), parseInt(p.color.slice(3, 5), 16), parseInt(p.color.slice(5, 7), 16)];
        p.trail.forEach((pt, i) => { ctx.beginPath(); ctx.arc(pt.x, pt.y, p.size * (i / p.trail.length), 0, 6.28); ctx.fillStyle = `rgba(${r},${g},${b},${i / p.trail.length * 0.4})`; ctx.fill(); });
        ctx.beginPath(); ctx.arc(p.x, p.y, p.size, 0, 6.28); ctx.fillStyle = p.color; ctx.fill();
        ctx.beginPath(); ctx.arc(p.x, p.y, p.size * 3, 0, 6.28); ctx.fillStyle = `rgba(${r},${g},${b},0.1)`; ctx.fill();
      }

      // Nodes
      nodes.forEach(n => {
        const pulse = Math.sin(t * 0.002 + n.phase) * 0.5 + 0.5;
        n.glow *= 0.97;
        if (n.glow > 0.05) {
          const [r, g, b] = [parseInt(n.color.slice(1, 3), 16), parseInt(n.color.slice(3, 5), 16), parseInt(n.color.slice(5, 7), 16)];
          const gd = ctx.createRadialGradient(n.x, n.y, n.r, n.x, n.y, n.r * 3);
          gd.addColorStop(0, `rgba(${r},${g},${b},${n.glow * 0.3})`); gd.addColorStop(1, `rgba(${r},${g},${b},0)`);
          ctx.beginPath(); ctx.arc(n.x, n.y, n.r * 3, 0, 6.28); ctx.fillStyle = gd; ctx.fill();
        }
        ctx.beginPath(); ctx.arc(n.x, n.y, n.r + 2 + pulse * 2, 0, 6.28); ctx.strokeStyle = n.color + '30'; ctx.lineWidth = 1; ctx.stroke();
        ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, 6.28);
        const bg = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, n.r);
        bg.addColorStop(0, '#1a1a2e'); bg.addColorStop(1, '#0e0e18');
        ctx.fillStyle = bg; ctx.fill(); ctx.strokeStyle = n.color + '60'; ctx.lineWidth = 2; ctx.stroke();
        ctx.font = `${n.r * 0.8}px serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(n.icon, n.x, n.y);
        ctx.font = '500 10px IBM Plex Mono, monospace'; ctx.fillStyle = 'rgba(255,255,255,0.27)'; ctx.fillText(n.name, n.x, n.y + n.r + 16);
      });

      // Ambient stars
      for (let i = 0; i < 50; i++) {
        ctx.beginPath(); ctx.arc((i * 137.5 + t * 0.01) % W, (i * 97.3 + t * 0.005) % H, 0.7, 0, 6.28);
        ctx.fillStyle = `rgba(201,164,78,${(Math.sin(t * 0.003 + i) * 0.3 + 0.3) * 0.1})`; ctx.fill();
      }

      animRef.current = requestAnimationFrame(draw);
    };

    animRef.current = requestAnimationFrame(draw);
    return () => { cancelAnimationFrame(animRef.current); window.removeEventListener('resize', resize); };
  }, [canvasRef, initNodes]);

  return { spawnParticle };
}
