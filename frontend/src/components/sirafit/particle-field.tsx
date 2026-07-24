import { useEffect, useRef } from "react";

interface Particle {
  x: number;
  y: number;
  z: number;
  size: number;
  opacity: number;
  hue: number;
}

export function ParticleField() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationId: number;
    let particles: Particle[] = [];
    let time = 0;

    const DPR = window.devicePixelRatio || 1;
    const PARTICLE_COUNT = 130;
    const CONNECTION_DIST = 120;
    const SPHERE_RADIUS = 220;

    function resize() {
      const w = window.innerWidth;
      const h = canvas!.parentElement?.offsetHeight || window.innerHeight;
      canvas!.width = w * DPR;
      canvas!.height = h * DPR;
      canvas!.style.width = `${w}px`;
      canvas!.style.height = `${h}px`;
      ctx!.setTransform(DPR, 0, 0, DPR, 0, 0);
    }

    function initParticles() {
      particles = [];
      for (let i = 0; i < PARTICLE_COUNT; i++) {
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);
        const r = SPHERE_RADIUS * (0.4 + Math.random() * 0.6);

        particles.push({
          x: Math.sin(phi) * Math.cos(theta) * r,
          y: Math.sin(phi) * Math.sin(theta) * r,
          z: Math.cos(phi) * r,
          size: 1 + Math.random() * 2,
          opacity: 0.3 + Math.random() * 0.5,
          hue: 220 + Math.random() * 40,
        });
      }
    }

    function animate() {
      const w = canvas!.width / DPR;
      const h = canvas!.height / DPR;
      const cx = w / 2;
      const cy = h / 2;

      ctx!.clearRect(0, 0, w, h);

      time += 0.003;

      // Slow Y-axis rotation of the entire field
      const rotY = time * 0.3;

      // Build rotated + depth-sorted array — avoids allocating per frame in a pool
      const projected = particles
        .map((p) => {
          const rx = p.x * Math.cos(rotY) - p.z * Math.sin(rotY);
          const rz = p.x * Math.sin(rotY) + p.z * Math.cos(rotY);
          const scale = 800 / (800 + rz);
          return {
            px: cx + rx * scale,
            py: cy + p.y * scale,
            rz,
            size: p.size * scale,
            opacity: p.opacity * (0.5 + scale * 0.5),
            hue: p.hue,
          };
        })
        .sort((a, b) => a.rz - b.rz);

      // Draw connections between close particles
      for (let i = 0; i < projected.length; i++) {
        const a = projected[i];
        for (let j = i + 1; j < projected.length; j++) {
          const b = projected[j];
          const dx = a.px - b.px;
          const dy = a.py - b.py;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < CONNECTION_DIST) {
            const alpha = (1 - dist / CONNECTION_DIST) * 0.12;
            ctx!.beginPath();
            ctx!.moveTo(a.px, a.py);
            ctx!.lineTo(b.px, b.py);
            ctx!.strokeStyle = `hsla(220, 50%, 70%, ${alpha})`;
            ctx!.lineWidth = 0.5;
            ctx!.stroke();
          }
        }
      }

      // Draw particles
      for (const p of projected) {
        ctx!.beginPath();
        ctx!.arc(p.px, p.py, p.size, 0, Math.PI * 2);
        ctx!.fillStyle = `hsla(${p.hue}, 60%, 60%, ${p.opacity})`;
        ctx!.fill();

        // Subtle glow on larger particles
        if (p.size > 1.5) {
          ctx!.beginPath();
          ctx!.arc(p.px, p.py, p.size * 2.5, 0, Math.PI * 2);
          ctx!.fillStyle = `hsla(${p.hue}, 60%, 60%, ${p.opacity * 0.08})`;
          ctx!.fill();
        }
      }

      animationId = requestAnimationFrame(animate);
    }

    resize();
    initParticles();
    animate();

    window.addEventListener("resize", resize);

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 pointer-events-none"
      style={{ zIndex: 0 }}
    />
  );
}
