import { useEffect, useRef } from "react";
import type { CSSProperties, RefObject } from "react";

type LineStyle = "solid" | "dashed" | "dotted";
type TargetEffect = "lock" | "glitch" | "none";

interface CrosshairProps {
  color?: string;
  containerRef?: RefObject<HTMLElement | null> | null;
  thickness?: number;
  opacity?: number;
  lineStyle?: LineStyle;
  gap?: number;
  fade?: number;
  smoothing?: number;
  showCoordinates?: boolean;
  targetEffect?: TargetEffect;
  targetSelector?: string;
  clickPulse?: boolean;
  blendMode?: CSSProperties["mixBlendMode"];
  className?: string;
  style?: CSSProperties;
}

interface Pulse {
  x: number;
  y: number;
  age: number;
}

interface Frame {
  x: number;
  y: number;
  width: number;
  height: number;
  alpha: number;
}

const clamp = (value: number, min: number, max: number) =>
  Math.min(max, Math.max(min, value));

export default function Crosshair({
  color = "#b23636",
  containerRef = null,
  thickness = 1,
  opacity = 0.85,
  lineStyle = "solid",
  gap = 0,
  fade = 0,
  smoothing = 0.35,
  showCoordinates = true,
  targetEffect = "lock",
  targetSelector = "a, button, [data-crosshair-target]",
  clickPulse = true,
  blendMode = "normal",
  className = "",
  style,
}: CrosshairProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const settingsRef = useRef({
    color,
    thickness: clamp(thickness, 0.5, 8),
    opacity: clamp(opacity, 0, 1),
    lineStyle,
    gap: Math.max(0, gap),
    fade: clamp(fade, 0, 1),
    smoothing: clamp(smoothing, 0, 1),
    showCoordinates,
    targetEffect,
    targetSelector,
    clickPulse,
  });

  settingsRef.current = {
    color,
    thickness: clamp(thickness, 0.5, 8),
    opacity: clamp(opacity, 0, 1),
    lineStyle,
    gap: Math.max(0, gap),
    fade: clamp(fade, 0, 1),
    smoothing: clamp(smoothing, 0, 1),
    showCoordinates,
    targetEffect,
    targetSelector,
    clickPulse,
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    const host = containerRef?.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !host || !context) return;

    const reducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    const pointer = {
      x: 0,
      y: 0,
      targetX: 0,
      targetY: 0,
      inside: false,
      target: null as Element | null,
      frame: { x: 0, y: 0, width: 0, height: 0, alpha: 0 } satisfies Frame,
      frameAnimating: false,
      pulses: [] as Pulse[],
    };
    const bounds = { width: 0, height: 0, ratio: 1 };
    let requestId = 0;
    let previousTime = 0;
    let mounted = true;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      bounds.ratio = Math.min(window.devicePixelRatio || 1, 2);
      bounds.width = rect.width;
      bounds.height = rect.height;
      canvas.width = Math.max(1, Math.round(rect.width * bounds.ratio));
      canvas.height = Math.max(1, Math.round(rect.height * bounds.ratio));
      schedule();
    };

    const getTarget = (element: EventTarget | null): Element | null => {
      if (settingsRef.current.targetEffect === "none" || !(element instanceof Element)) {
        return null;
      }
      const target = element.closest(settingsRef.current.targetSelector);
      return target && host.contains(target) ? target : null;
    };

    const pointerMove = (event: PointerEvent) => {
      if (event.pointerType === "touch" && event.buttons === 0) return;
      const rect = canvas.getBoundingClientRect();
      pointer.targetX = event.clientX - rect.left;
      pointer.targetY = event.clientY - rect.top;
      pointer.inside = true;
      const nextTarget = getTarget(event.target);
      if (nextTarget !== pointer.target) pointer.frameAnimating = true;
      pointer.target = nextTarget;
      schedule();
    };

    const pointerLeave = () => {
      pointer.inside = false;
      pointer.target = null;
      schedule();
    };

    const pointerDown = (event: PointerEvent) => {
      pointerMove(event);
      if (!settingsRef.current.clickPulse || reducedMotion) return;
      pointer.pulses.push({
        x: pointer.targetX,
        y: pointer.targetY,
        age: 0,
      });
      schedule();
    };

    const drawLabel = (text: string, x: number, y: number) => {
      context.font = "500 9px ui-monospace, SFMono-Regular, Menlo, monospace";
      const width = context.measureText(text).width + 8;
      const left = clamp(x - width / 2, 3, bounds.width - width - 3);
      const top = clamp(y, 3, bounds.height - 16);
      context.fillStyle = settingsRef.current.color;
      context.beginPath();
      context.roundRect(left, top, width, 14, 3);
      context.fill();
      context.fillStyle = "#2d3424";
      context.textAlign = "center";
      context.textBaseline = "middle";
      context.fillText(text, left + width / 2, top + 7);
    };

    const drawLine = (
      x1: number,
      y1: number,
      x2: number,
      y2: number,
      horizontal: boolean,
      fadeAmount: number,
    ) => {
      if (horizontal ? x2 <= x1 : y2 <= y1) return;
      context.beginPath();
      if (fadeAmount > 0) {
        const gradient = horizontal
          ? context.createLinearGradient(0, 0, bounds.width, 0)
          : context.createLinearGradient(0, 0, 0, bounds.height);
        const position = horizontal
          ? pointer.x / Math.max(bounds.width, 1)
          : pointer.y / Math.max(bounds.height, 1);
        gradient.addColorStop(0, `${settingsRef.current.color}00`);
        gradient.addColorStop(clamp(position, 0.01, 0.99), settingsRef.current.color);
        gradient.addColorStop(1, `${settingsRef.current.color}00`);
        context.strokeStyle = gradient;
      } else {
        context.strokeStyle = settingsRef.current.color;
      }
      if (horizontal) {
        context.moveTo(x1, y1);
        context.lineTo(x2, y2);
      } else {
        context.moveTo(x1, y1);
        context.lineTo(x2, y2);
      }
      context.stroke();
    };

    const draw = (delta: number) => {
      const settings = settingsRef.current;
      context.setTransform(bounds.ratio, 0, 0, bounds.ratio, 0, 0);
      context.clearRect(0, 0, bounds.width, bounds.height);

      const easing = reducedMotion
        ? 1
        : 1 - Math.exp(-delta / (0.008 + settings.smoothing * 0.16));
      pointer.x += (pointer.targetX - pointer.x) * easing;
      pointer.y += (pointer.targetY - pointer.y) * easing;

      const frame = pointer.frame;
      let targetRect: DOMRect | null = null;
      if (pointer.inside && pointer.target && settings.targetEffect === "lock") {
        targetRect = pointer.target.getBoundingClientRect();
        const hostRect = host.getBoundingClientRect();
        const next = {
          x: targetRect.left - hostRect.left - 5,
          y: targetRect.top - hostRect.top - 5,
          width: targetRect.width + 10,
          height: targetRect.height + 10,
          alpha: 1,
        };
        const frameEase = reducedMotion ? 1 : 1 - Math.exp(-delta / 0.085);
        frame.x += (next.x - frame.x) * frameEase;
        frame.y += (next.y - frame.y) * frameEase;
        frame.width += (next.width - frame.width) * frameEase;
        frame.height += (next.height - frame.height) * frameEase;
        frame.alpha += (1 - frame.alpha) * frameEase;
        pointer.frameAnimating =
          Math.abs(next.x - frame.x) > 0.1 ||
          Math.abs(next.y - frame.y) > 0.1 ||
          Math.abs(next.width - frame.width) > 0.1 ||
          Math.abs(next.height - frame.height) > 0.1 ||
          Math.abs(1 - frame.alpha) > 0.002;
      } else {
        const frameEase = reducedMotion ? 1 : 1 - Math.exp(-delta / 0.14);
        frame.alpha += (0 - frame.alpha) * frameEase;
        pointer.frameAnimating = frame.alpha > 0.002;
      }

      context.globalAlpha = settings.opacity * (pointer.inside ? 1 : 0);
      context.lineWidth = settings.thickness;
      context.lineCap = settings.lineStyle === "dotted" ? "round" : "butt";
      context.setLineDash(
        settings.lineStyle === "dotted"
          ? [0, settings.thickness * 4]
          : settings.lineStyle === "dashed"
            ? [settings.thickness * 6, settings.thickness * 5]
            : [],
      );
      const gapSize = settings.gap;
      drawLine(0, pointer.y, pointer.x - gapSize, pointer.y, true, settings.fade);
      drawLine(pointer.x + gapSize, pointer.y, bounds.width, pointer.y, true, settings.fade);
      drawLine(pointer.x, 0, pointer.x, pointer.y - gapSize, false, settings.fade);
      drawLine(pointer.x, pointer.y + gapSize, pointer.x, bounds.height, false, settings.fade);

      if (frame.alpha > 0.01) {
        context.globalAlpha = frame.alpha * settings.opacity;
        context.lineWidth = Math.max(1.5, settings.thickness);
        context.setLineDash([]);
        const arm = Math.min(12, frame.width / 3, frame.height / 3);
        context.beginPath();
        context.moveTo(frame.x, frame.y + arm);
        context.lineTo(frame.x, frame.y);
        context.lineTo(frame.x + arm, frame.y);
        context.moveTo(frame.x + frame.width - arm, frame.y);
        context.lineTo(frame.x + frame.width, frame.y);
        context.lineTo(frame.x + frame.width, frame.y + arm);
        context.moveTo(frame.x + frame.width, frame.y + frame.height - arm);
        context.lineTo(frame.x + frame.width, frame.y + frame.height);
        context.lineTo(frame.x + frame.width - arm, frame.y + frame.height);
        context.moveTo(frame.x + arm, frame.y + frame.height);
        context.lineTo(frame.x, frame.y + frame.height);
        context.lineTo(frame.x, frame.y + frame.height - arm);
        context.stroke();
      }

      if (pointer.inside && settings.showCoordinates && !targetRect) {
        context.globalAlpha = settings.opacity;
        drawLabel(`${Math.round(pointer.x)}, ${Math.round(pointer.y)}`, pointer.x, 7);
      }

      pointer.pulses = pointer.pulses.filter((pulse) => {
        pulse.age += delta;
        const progress = pulse.age / 0.55;
        if (progress >= 1) return false;
        context.globalAlpha = (1 - progress) ** 2 * settings.opacity;
        context.lineWidth = Math.max(1, settings.thickness);
        context.setLineDash([]);
        context.beginPath();
        context.arc(pulse.x, pulse.y, 3 + 30 * (1 - (1 - progress) ** 3), 0, Math.PI * 2);
        context.stroke();
        return true;
      });
      context.globalAlpha = 1;
      context.setLineDash([]);
    };

    const tick = (time: number) => {
      requestId = 0;
      if (!mounted) return;
      const delta = previousTime
        ? Math.min(0.05, Math.max(0.001, (time - previousTime) / 1000))
        : 0.016;
      previousTime = time;
      draw(delta);

      const settling =
        Math.abs(pointer.targetX - pointer.x) > 0.05 ||
        Math.abs(pointer.targetY - pointer.y) > 0.05 ||
        pointer.frameAnimating ||
        pointer.pulses.length > 0;
      if (settling) schedule();
    };

    function schedule() {
      if (!requestId && mounted) requestId = requestAnimationFrame(tick);
    }

    const observer = new ResizeObserver(resize);
    observer.observe(canvas);
    host.addEventListener("pointermove", pointerMove);
    host.addEventListener("pointerdown", pointerDown);
    host.addEventListener("pointerleave", pointerLeave);
    resize();

    return () => {
      mounted = false;
      cancelAnimationFrame(requestId);
      observer.disconnect();
      host.removeEventListener("pointermove", pointerMove);
      host.removeEventListener("pointerdown", pointerDown);
      host.removeEventListener("pointerleave", pointerLeave);
    };
  }, [containerRef]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className={className}
      style={{
        position: "absolute",
        inset: 0,
        width: "100%",
        height: "100%",
        pointerEvents: "none",
        zIndex: 3,
        mixBlendMode: blendMode,
        ...style,
      }}
    />
  );
}
