import { useEffect, useRef, useState } from "react";
import type { Grid } from "../api/types";
import { sampleRamp, rampGradient, type RampName } from "./colourScales";

// Drawn FACE-ON, the way a launch monitor draws an impact pattern and the way
// a driver is photographed: +x rightward is the HEEL, so the toe is on the
// left. This matches forgiveness_diagram.py exactly -- the same map should not
// change handedness depending on which view you open it in.

export interface HoverPoint {
  column: number;
  row: number;
  xMm: number;
  yMm: number;
}

interface Props {
  xMm: number[];
  yMm: number[];
  values: Grid;
  onFace: boolean[][];
  ramp: RampName;
  diverging?: boolean;
  unit: string;
  /** Draw a contour around cells at or above this value (the threshold). */
  contourAtLeast?: number | null;
  frictionFlags?: boolean[][];
  topspinFlags?: boolean[][];
  sweetSpotMm?: [number, number];
  faceCentreMm?: [number, number];
  showFlags: boolean;
  showMarkers: boolean;
  hover: HoverPoint | null;
  pinned: HoverPoint | null;
  onHover: (point: HoverPoint | null) => void;
  onPin: (point: HoverPoint | null) => void;
}

function extent(values: Grid, onFace: boolean[][], diverging: boolean) {
  let low = Infinity;
  let high = -Infinity;
  for (let row = 0; row < values.length; row += 1) {
    for (let column = 0; column < values[row].length; column += 1) {
      const value = values[row][column];
      if (value === null || !onFace[row][column]) continue;
      if (value < low) low = value;
      if (value > high) high = value;
    }
  }
  if (!Number.isFinite(low) || !Number.isFinite(high)) return { low: 0, high: 1 };
  if (diverging) {
    // A diverging scale must be centred on zero, or the colour lies about
    // which side of neutral a cell is on.
    const reach = Math.max(Math.abs(low), Math.abs(high)) || 1;
    return { low: -reach, high: reach };
  }
  if (low === high) return { low, high: low + 1 };
  return { low, high };
}

export function ForgivenessHeatmap(props: Props) {
  const {
    xMm, yMm, values, onFace, ramp, diverging = false, unit,
    contourAtLeast = null, frictionFlags, topspinFlags,
    sweetSpotMm, faceCentreMm, showFlags, showMarkers,
    hover, pinned, onHover, onPin,
  } = props;

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [width, setWidth] = useState(680);

  const spacingX = xMm.length > 1 ? xMm[1] - xMm[0] : 1;
  const spacingY = yMm.length > 1 ? yMm[1] - yMm[0] : 1;
  const spanX = (xMm[xMm.length - 1] - xMm[0]) + spacingX;
  const spanY = (yMm[yMm.length - 1] - yMm[0]) + spacingY;

  const padding = { left: 46, right: 14, top: 12, bottom: 38 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = Math.round(plotWidth * (spanY / spanX));
  const height = plotHeight + padding.top + padding.bottom;

  // Millimetres to canvas pixels. y is flipped because canvas y grows
  // downward while the crown is up.
  const toPixelX = (mm: number) => padding.left + ((mm - xMm[0] + spacingX / 2) / spanX) * plotWidth;
  const toPixelY = (mm: number) => padding.top + plotHeight - ((mm - yMm[0] + spacingY / 2) / spanY) * plotHeight;

  useEffect(() => {
    function measure() {
      const parent = canvasRef.current?.parentElement;
      if (parent) setWidth(Math.max(320, Math.min(760, parent.clientWidth)));
    }
    measure();
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, []);

  // Deliberately no dependency array: the canvas is redrawn on every render.
  // Everything it draws -- the grid, the hover cell, the pinned cell, the
  // threshold contour, the overlays -- can change independently, and listing
  // them all would be the same thing written at more length and with more
  // ways to forget one. The grid is ~1600 filled rectangles, which is far
  // below the cost of a React render.
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const context = canvas.getContext("2d");
    if (!context) return;

    const ratio = window.devicePixelRatio || 1;
    canvas.width = width * ratio;
    canvas.height = height * ratio;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    context.clearRect(0, 0, width, height);

    const { low, high } = extent(values, onFace, diverging);
    const cellWidth = plotWidth / xMm.length;
    const cellHeight = plotHeight / yMm.length;

    for (let row = 0; row < yMm.length; row += 1) {
      for (let column = 0; column < xMm.length; column += 1) {
        const value = values[row]?.[column];
        if (value === null || value === undefined || !onFace[row]?.[column]) continue;
        context.fillStyle = sampleRamp(ramp, (value - low) / (high - low));
        context.fillRect(
          padding.left + column * cellWidth,
          padding.top + plotHeight - (row + 1) * cellHeight,
          Math.ceil(cellWidth) + 0.5,
          Math.ceil(cellHeight) + 0.5,
        );
      }
    }

    // Threshold contour: outline the boundary of the region at or above the
    // threshold by stroking only the edges where a cell's neighbour differs.
    // Recomputed here rather than on the server, so dragging the slider
    // updates instantly with no round trip.
    if (contourAtLeast !== null) {
      context.strokeStyle = "rgba(255,255,255,0.95)";
      context.lineWidth = 1.6;
      context.beginPath();
      const inside = (row: number, column: number) => {
        const value = values[row]?.[column];
        return (
          value !== null && value !== undefined &&
          onFace[row]?.[column] === true && value >= contourAtLeast
        );
      };
      for (let row = 0; row < yMm.length; row += 1) {
        for (let column = 0; column < xMm.length; column += 1) {
          if (!inside(row, column)) continue;
          const left = padding.left + column * cellWidth;
          const top = padding.top + plotHeight - (row + 1) * cellHeight;
          if (!inside(row, column - 1)) { context.moveTo(left, top); context.lineTo(left, top + cellHeight); }
          if (!inside(row, column + 1)) { context.moveTo(left + cellWidth, top); context.lineTo(left + cellWidth, top + cellHeight); }
          if (!inside(row + 1, column)) { context.moveTo(left, top); context.lineTo(left + cellWidth, top); }
          if (!inside(row - 1, column)) { context.moveTo(left, top + cellHeight); context.lineTo(left + cellWidth, top + cellHeight); }
        }
      }
      context.stroke();
    }

    if (showFlags) {
      // Where the model has stopped being trustworthy. Same meanings as the
      // matplotlib figure: dots for "needs more friction than the sourced
      // coefficient", rings for "the flat face has produced topspin".
      for (let row = 0; row < yMm.length; row += 1) {
        for (let column = 0; column < xMm.length; column += 1) {
          const centreX = toPixelX(xMm[column]);
          const centreY = toPixelY(yMm[row]);
          if (frictionFlags?.[row]?.[column]) {
            context.fillStyle = "rgba(0,0,0,0.85)";
            context.beginPath();
            context.arc(centreX, centreY, 1.7, 0, Math.PI * 2);
            context.fill();
          }
          if (topspinFlags?.[row]?.[column]) {
            context.strokeStyle = "rgba(0,0,0,0.85)";
            context.lineWidth = 1;
            context.beginPath();
            context.arc(centreX, centreY, 3, 0, Math.PI * 2);
            context.stroke();
          }
        }
      }
    }

    if (showMarkers) {
      if (faceCentreMm) {
        const [x, y] = faceCentreMm;
        const centreX = toPixelX(x);
        const centreY = toPixelY(y);
        context.strokeStyle = "#111";
        context.lineWidth = 2.4;
        context.beginPath();
        context.moveTo(centreX - 6, centreY - 6);
        context.lineTo(centreX + 6, centreY + 6);
        context.moveTo(centreX + 6, centreY - 6);
        context.lineTo(centreX - 6, centreY + 6);
        context.stroke();
      }
      if (sweetSpotMm) {
        const [x, y] = sweetSpotMm;
        drawStar(context, toPixelX(x), toPixelY(y), 9);
      }
    }

    for (const [point, colour, lineWidth] of [
      [pinned, "#ff6b00", 2.4] as const,
      [hover, "#ffffff", 1.8] as const,
    ]) {
      if (!point) continue;
      context.strokeStyle = colour;
      context.lineWidth = lineWidth;
      context.strokeRect(
        padding.left + point.column * cellWidth - 0.5,
        padding.top + plotHeight - (point.row + 1) * cellHeight - 0.5,
        cellWidth + 1,
        cellHeight + 1,
      );
    }

    // Axes. The colour comes from the app's own theme variable so the labels
    // stay readable in dark mode -- the canvas has no stylesheet of its own,
    // so anything hardcoded here would be invisible in one theme or the other.
    context.fillStyle = themeColour("--text-muted", "#5a5a5a");
    context.font = "10px system-ui, sans-serif";
    context.textAlign = "center";
    for (const tick of axisTicks(xMm)) {
      context.fillText(`${tick}`, toPixelX(tick), padding.top + plotHeight + 14);
    }
    context.fillText("toe  ←   strike position (mm)   →  heel",
      padding.left + plotWidth / 2, padding.top + plotHeight + 30);
    context.textAlign = "right";
    for (const tick of axisTicks(yMm)) {
      context.fillText(`${tick}`, padding.left - 6, toPixelY(tick) + 3);
    }
    context.save();
    context.translate(11, padding.top + plotHeight / 2);
    context.rotate(-Math.PI / 2);
    context.textAlign = "center";
    context.fillText("sole  ←  height (mm)  →  crown", 0, 0);
    context.restore();
  });

  function pointFromEvent(event: React.MouseEvent<HTMLCanvasElement>): HoverPoint | null {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    const bounds = canvas.getBoundingClientRect();
    const offsetX = event.clientX - bounds.left - padding.left;
    const offsetY = event.clientY - bounds.top - padding.top;
    if (offsetX < 0 || offsetY < 0 || offsetX > plotWidth || offsetY > plotHeight) return null;

    const column = Math.floor((offsetX / plotWidth) * xMm.length);
    const row = Math.floor(((plotHeight - offsetY) / plotHeight) * yMm.length);
    if (column < 0 || column >= xMm.length || row < 0 || row >= yMm.length) return null;
    if (!onFace[row]?.[column]) return null;
    return { column, row, xMm: xMm[column], yMm: yMm[row] };
  }

  const { low, high } = extent(values, onFace, diverging);

  return (
    <div className="heatmap">
      <canvas
        ref={canvasRef}
        className="heatmap-canvas"
        onMouseMove={(event) => onHover(pointFromEvent(event))}
        onMouseLeave={() => onHover(null)}
        onClick={(event) => {
          const point = pointFromEvent(event);
          const samePoint = point && pinned &&
            point.row === pinned.row && point.column === pinned.column;
          onPin(samePoint ? null : point);
        }}
      />
      <div className="colour-bar">
        <span>{formatTick(low)}</span>
        <span className="colour-bar-ramp" style={{ background: rampGradient(ramp) }} />
        <span>{formatTick(high)}</span>
        <em>{unit}</em>
      </div>
    </div>
  );
}

/**
 * Read one of the app's CSS custom properties for use on the canvas.
 *
 * Canvas drawing takes literal colours, so it cannot inherit the theme the
 * way the surrounding DOM does. Pulling the variable off the document keeps
 * the two in step instead of hardcoding a colour that only works in one.
 */
function themeColour(variable: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  const value = getComputedStyle(document.documentElement)
    .getPropertyValue(variable)
    .trim();
  return value || fallback;
}

function drawStar(context: CanvasRenderingContext2D, x: number, y: number, radius: number) {
  context.beginPath();
  for (let point = 0; point < 10; point += 1) {
    const reach = point % 2 === 0 ? radius : radius * 0.45;
    const angle = (Math.PI / 5) * point - Math.PI / 2;
    const pointX = x + Math.cos(angle) * reach;
    const pointY = y + Math.sin(angle) * reach;
    if (point === 0) context.moveTo(pointX, pointY);
    else context.lineTo(pointX, pointY);
  }
  context.closePath();
  context.fillStyle = "#ffffff";
  context.fill();
  context.strokeStyle = "#111";
  context.lineWidth = 1;
  context.stroke();
}

function axisTicks(axis: number[]): number[] {
  const span = axis[axis.length - 1] - axis[0];
  const step = span > 80 ? 20 : span > 40 ? 10 : 5;
  const ticks: number[] = [];
  for (let value = Math.ceil(axis[0] / step) * step; value <= axis[axis.length - 1]; value += step) {
    ticks.push(value);
  }
  return ticks;
}

function formatTick(value: number): string {
  if (Math.abs(value) >= 100) return value.toFixed(0);
  if (Math.abs(value) >= 10) return value.toFixed(1);
  return value.toFixed(2);
}
