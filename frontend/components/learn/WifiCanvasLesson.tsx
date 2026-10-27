"use client";

import { useEffect, useRef, useState } from "react";
import {
  getWallAttenuation,
  WALL_ATTENUATION_DB,
  WALL_MATERIAL_LABELS,
  WIFI_BANDS,
  type WallMaterial,
  type WifiBand,
} from "./wallAttenuation";

export type WifiLessonScene =
  | "qam"
  | "ofdm"
  | "csma"
  | "spectrum"
  | "transmission"
  | "walls"
  | "dataJourney";

type Material = WallMaterial;
type CanvasState = {
  view: string;
  noise: boolean;
  wall: boolean;
  material: Material;
  band: WifiBand;
  multipleWalls: boolean;
  devices: number;
  forceCollision: boolean;
  sentData: boolean;
  stepByStep: boolean;
  journeyStep: number;
  speed: "normal" | "fast";
};

const WIDTH = 760;
const HEIGHT = 390;
const INK = "#e2e8f0";
const MUTED = "#94a3b8";
const GRID = "rgba(148, 163, 184, 0.18)";
const BLUE = "#60a5fa";
const TEAL = "#34d399";
const VIOLET = "#a78bfa";
const AMBER = "#fbbf24";
const MATERIAL_COLORS: Record<Material, string> = {
  glass: "#38bdf8",
  drywall: "#d6a85f",
  wood: "#b77943",
  brick: "#c26952",
  concrete: "#64748b",
  metal: "#94a3b8",
  unknown: "#7c8b9c",
};

function label(ctx: CanvasRenderingContext2D, text: string, x: number, y: number, color = INK, size = 14) {
  ctx.fillStyle = color;
  ctx.font = `500 ${size}px system-ui, sans-serif`;
  ctx.fillText(text, x, y);
}

function roundedBox(ctx: CanvasRenderingContext2D, x: number, y: number, width: number, height: number, color: string) {
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.roundRect(x, y, width, height, 8);
  ctx.fill();
}

function drawGrid(ctx: CanvasRenderingContext2D) {
  ctx.strokeStyle = GRID;
  ctx.lineWidth = 1;
  for (let x = 36; x < WIDTH; x += 48) {
    ctx.beginPath();
    ctx.moveTo(x, 32);
    ctx.lineTo(x, HEIGHT - 32);
    ctx.stroke();
  }
  for (let y = 40; y < HEIGHT; y += 44) {
    ctx.beginPath();
    ctx.moveTo(32, y);
    ctx.lineTo(WIDTH - 32, y);
    ctx.stroke();
  }
}

function drawQam(ctx: CanvasRenderingContext2D, time: number, state: CanvasState) {
  const order = Number(state.view);
  const side = order === 2 ? 2 : Math.sqrt(order);
  const rowCount = order === 2 ? 1 : side;
  const columnCount = side;
  const centerX = 250;
  const centerY = 190;
  const radius = 126;
  const points = order;
  drawGrid(ctx);

  ctx.strokeStyle = "rgba(148,163,184,.55)";
  ctx.beginPath();
  ctx.moveTo(centerX - radius - 12, centerY);
  ctx.lineTo(centerX + radius + 12, centerY);
  ctx.moveTo(centerX, centerY - radius - 12);
  ctx.lineTo(centerX, centerY + radius + 12);
  ctx.stroke();
  label(ctx, "Q", centerX - 142, centerY - 136, MUTED, 12);
  label(ctx, "I", centerX + 137, centerY + 17, MUTED, 12);

  for (let row = 0; row < rowCount; row += 1) {
    for (let col = 0; col < columnCount; col += 1) {
      const x = centerX + ((col / (columnCount - 1)) * 2 - 1) * radius;
      const y = order === 2 ? centerY : centerY + ((row / (rowCount - 1)) * 2 - 1) * radius;
      const wobbleX = state.noise ? Math.sin(row * 19 + col * 7) * 5 : 0;
      const wobbleY = state.noise ? Math.cos(row * 13 + col * 11) * 5 : 0;
      ctx.fillStyle = state.noise ? "#fb7185" : BLUE;
      ctx.beginPath();
      ctx.arc(x + wobbleX, y + wobbleY, order > 256 ? 2.1 : 3.2, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  const active = Math.floor((time * 1.7) % points);
  const activeX = centerX + (((active % columnCount) / (columnCount - 1)) * 2 - 1) * radius;
  const activeY = order === 2 ? centerY : centerY + ((Math.floor(active / columnCount) / (rowCount - 1)) * 2 - 1) * radius;
  const inPhase = (active % columnCount) / (columnCount - 1) * 2 - 1;
  const quadrature = order === 2 ? 0 : Math.floor(active / columnCount) / (rowCount - 1) * 2 - 1;
  const amplitude = Math.hypot(inPhase, quadrature);
  const phaseDegrees = Math.atan2(quadrature, inPhase) * 180 / Math.PI;
  ctx.strokeStyle = AMBER;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(activeX, activeY, 9, 0, Math.PI * 2);
  ctx.stroke();
  label(ctx, "Constelación: cada punto representa un símbolo", 58, 348, MUTED, 12);

  roundedBox(ctx, 440, 82, 274, 218, "rgba(15,23,42,.68)");
  label(ctx, order === 2 ? "BPSK" : `${order}-QAM`, 464, 115, VIOLET, 22);
  label(ctx, `${order === 2 ? 1 : Math.log2(order)} bits por símbolo`, 464, 146, INK, 15);
  label(ctx, state.noise ? "SNR bajo: puntos dispersos" : "Señal limpia: puntos definidos", 464, 176, state.noise ? "#fda4af" : TEAL, 13);
  ctx.strokeStyle = state.noise ? "#fb7185" : BLUE;
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  for (let x = 462; x <= 690; x += 2) {
    const t = (x - 462) / 228;
    const y = 232 - Math.sin(t * Math.PI * 6 + time * 3) * (state.noise ? 27 : 40);
    if (x === 462) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();
  label(ctx, "Forma de onda modulada", 464, 282, MUTED, 12);
  label(ctx, `Amplitud normalizada: ${amplitude.toFixed(2)}`, 464, 317, INK, 12);
  label(ctx, `Fase: ${phaseDegrees.toFixed(0)}°`, 464, 337, INK, 12);
  label(ctx, "Más bits por símbolo requieren mejor SNR.", 58, 372, INK, 13);
}

function drawOfdm(ctx: CanvasRenderingContext2D, time: number, state: CanvasState) {
  drawGrid(ctx);
  const ofdma = state.view === "ofdma";
  const single = state.view === "single";
  label(ctx, single ? "Una portadora ocupa el canal" : "Subportadoras ortogonales en paralelo", 52, 65, INK, 19);
  const x0 = 58;
  const chartWidth = 640;
  const bandY = 124;
  const bandHeight = ofdma ? 204 : 168;
  roundedBox(ctx, x0, bandY, chartWidth, bandHeight, "rgba(15,23,42,.7)");

  if (single) {
    ctx.strokeStyle = BLUE;
    ctx.lineWidth = 3;
    ctx.beginPath();
    for (let x = 0; x <= chartWidth; x += 2) {
      const y = bandY + bandHeight / 2 + Math.sin(x / chartWidth * Math.PI * 6 - time * 3) * 48;
      if (x === 0) ctx.moveTo(x0 + x, y);
      else ctx.lineTo(x0 + x, y);
    }
    ctx.stroke();
    label(ctx, "Portadora única", x0 + 14, bandY + bandHeight + 26, MUTED, 13);
  } else if (ofdma) {
    const users = [
      { name: "Cliente A", row: 0, color: BLUE },
      { name: "Cliente B", row: 1, color: TEAL },
      { name: "Cliente C", row: 2, color: VIOLET },
      { name: "Cliente D", row: 3, color: AMBER },
    ];
    const rowHeight = bandHeight / users.length;
    users.forEach((user, index) => {
      const y = bandY + index * rowHeight;
      roundedBox(ctx, x0 + 10, y + 5, chartWidth * 0.2, rowHeight - 10, user.color);
      label(ctx, user.name, x0 + 18, y + rowHeight / 2 + 5, "#0f172a", 12);
      for (let i = 0; i < 5; i += 1) {
        const ruX = x0 + chartWidth * (0.25 + i * 0.145);
        ctx.fillStyle = `${user.color}55`;
        ctx.fillRect(ruX, y + 8, chartWidth * 0.12, rowHeight - 16);
        if (i === Math.floor((time * 2 + index) % 5)) {
          ctx.fillStyle = user.color;
          ctx.fillRect(ruX, y + 8, chartWidth * 0.12, rowHeight - 16);
        }
      }
    });
    label(ctx, "Resource Units: varios clientes atendidos a la vez", 58, 357, MUTED, 13);
  } else {
    const count = 12;
    const subWidth = chartWidth / count;
    for (let i = 0; i < count; i += 1) {
      const left = x0 + i * subWidth;
      const color = [BLUE, TEAL, VIOLET, AMBER][i % 4];
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.7;
      ctx.beginPath();
      for (let x = 2; x < subWidth - 2; x += 1) {
        const y = bandY + bandHeight / 2 + Math.sin((x / subWidth) * Math.PI * 2 * (1 + i % 3) - time * 2 + i) * 26;
        if (x === 2) ctx.moveTo(left + x, y);
        else ctx.lineTo(left + x, y);
      }
      ctx.stroke();
      if (state.view === "ofdm-cp") {
        ctx.fillStyle = "rgba(251,191,36,.22)";
        ctx.fillRect(left + subWidth * 0.7, bandY + 8, subWidth * 0.25, bandHeight - 16);
      }
    }
    label(ctx, state.view === "ofdm-cp" ? "Prefijo cíclico (CP)" : "Cada tono cruza por cero en el pico de los demás", 58, 329, MUTED, 13);
    label(ctx, "Ortogonalidad: reduce la interferencia entre subportadoras.", 58, 357, INK, 13);
  }
  label(ctx, ofdma ? "Tiempo →" : "Frecuencia →", 628, 377, MUTED, 12);
}

function drawCsma(ctx: CanvasRenderingContext2D, time: number, state: CanvasState) {
  drawGrid(ctx);
  const collision = state.view === "collision";
  label(ctx, "Escuchar · esperar · transmitir · confirmar", 52, 64, INK, 19);
  const nodes = [
    { name: "Equipo A", y: 132, color: BLUE, offset: 0 },
    { name: "Equipo B", y: 220, color: TEAL, offset: collision ? 0 : 1.4 },
    { name: "Punto de acceso", y: 308, color: VIOLET, offset: 2.6 },
  ];
  nodes.forEach((node) => {
    roundedBox(ctx, 58, node.y - 22, 128, 44, node.color);
    label(ctx, node.name, 72, node.y + 5, "#0f172a", 13);
    ctx.strokeStyle = "rgba(148,163,184,.55)";
    ctx.beginPath();
    ctx.moveTo(190, node.y);
    ctx.lineTo(676, node.y);
    ctx.stroke();
    const phase = (time + node.offset) % 8;
    const transmitting = phase > 3 && phase < 5.8;
    const x = 222 + (phase / 8) * 400;
    roundedBox(ctx, x, node.y - 12, 82, 24, transmitting ? node.color : "rgba(51,65,85,.86)");
    label(ctx, transmitting ? "Datos →" : phase < 3 ? "Escuchando…" : "Backoff", x + 8, node.y + 5, transmitting ? "#0f172a" : INK, 11);
  });
  roundedBox(ctx, 210, 77, 390, 32, collision ? "rgba(251,113,133,.18)" : "rgba(52,211,153,.14)");
  label(ctx, collision ? "Colisión simulada: espera aleatoria y reintento" : "Canal compartido: los equipos esperan su turno", 226, 99, collision ? "#fda4af" : TEAL, 13);
  label(ctx, "CSMA/CA evita colisiones escuchando el canal y usando backoff aleatorio.", 52, 368, MUTED, 13);
}

function drawSpectrum(ctx: CanvasRenderingContext2D, time: number, state: CanvasState) {
  drawGrid(ctx);
  const zoom = state.view;
  label(ctx, "El espectro electromagnético: de ondas largas a cortas", 48, 58, INK, 19);
  const y = 135;
  if (zoom === "full") {
    const bands = [
      { text: "Radio", color: "#3b82f6", width: 118 },
      { text: "Microondas", color: "#14b8a6", width: 130 },
      { text: "Infrarrojo", color: "#22c55e", width: 114 },
      { text: "Visible", color: "#eab308", width: 94 },
      { text: "UV", color: "#f97316", width: 88 },
      { text: "Rayos X / γ", color: "#ef4444", width: 142 },
    ];
    let x = 38;
    bands.forEach((band) => {
      ctx.fillStyle = band.color;
      ctx.fillRect(x, y, band.width, 72);
      label(ctx, band.text, x + 9, y + 42, "#0f172a", 12);
      x += band.width;
    });
    label(ctx, "Wi-Fi está aquí →", 174, 242, TEAL, 14);
    ctx.strokeStyle = TEAL;
    ctx.beginPath();
    ctx.moveTo(273, 225);
    ctx.lineTo(273, 210);
    ctx.stroke();
    label(ctx, "Frecuencia creciente  →", 518, 252, MUTED, 12);
    label(ctx, "Longitud de onda decreciente  →", 44, 284, MUTED, 12);
  } else {
    const x0 = 72;
    const width = 620;
    const bands = zoom === "wifi"
      ? [
          { start: 0.04, end: 0.29, name: "2.4 GHz", color: BLUE },
          { start: 0.38, end: 0.72, name: "5 GHz", color: TEAL },
          { start: 0.76, end: 0.97, name: "6 GHz", color: VIOLET },
        ]
      : [
          { start: 0.08, end: 0.32, name: "Wi-Fi 2.4 GHz", color: BLUE },
          { start: 0.4, end: 0.72, name: "Wi-Fi 5 GHz", color: TEAL },
          { start: 0.77, end: 0.97, name: "Wi-Fi 6 GHz", color: VIOLET },
        ];
    ctx.fillStyle = "rgba(20,184,166,.2)";
    ctx.fillRect(x0, y, width, 92);
    label(ctx, "Microondas", x0 + 12, y + 24, MUTED, 12);
    bands.forEach((band) => {
      const x = x0 + width * band.start;
      const bandWidth = width * (band.end - band.start);
      ctx.fillStyle = band.color;
      ctx.fillRect(x, y + 38, bandWidth, 42);
      label(ctx, band.name, x + 6, y + 65, "#0f172a", 12);
    });
    label(ctx, zoom === "wifi" ? "Bandas Wi-Fi (vista ampliada)" : "Las bandas Wi-Fi ocupan una pequeña parte de las microondas", 72, 266, INK, 14);
    label(ctx, "Frecuencia creciente  →", 518, 310, MUTED, 12);
    ctx.strokeStyle = AMBER;
    const pulseX = x0 + ((time * 0.12) % 1) * width;
    ctx.beginPath();
    ctx.moveTo(pulseX, y - 15);
    ctx.lineTo(pulseX, y + 105);
    ctx.stroke();
  }
  label(ctx, `Banda seleccionada: ${state.band} GHz`, 48, 334, AMBER, 13);
  label(ctx, "Bandas sin licencia: las reglas y canales disponibles dependen del país.", 48, 357, MUTED, 12);
}

function drawTransmission(ctx: CanvasRenderingContext2D, time: number, state: CanvasState) {
  drawGrid(ctx);
  const band = state.view;
  const wavelength = band === "2.4" ? 12.5 : band === "5" ? 6 : 5;
  const amplitude = state.wall ? 16 : 34;
  const wallX = 390;
  label(ctx, "Un punto de acceso convierte datos en ondas de radio", 48, 62, INK, 19);
  roundedBox(ctx, 66, 156, 104, 88, "rgba(59,130,246,.88)");
  label(ctx, "Router", 88, 204, "#0f172a", 15);
  roundedBox(ctx, 590, 156, 104, 88, "rgba(52,211,153,.88)");
  label(ctx, "Cliente", 614, 204, "#0f172a", 15);
  if (state.wall) {
    ctx.fillStyle = "#64748b";
    ctx.fillRect(wallX - 14, 110, 28, 190);
    label(ctx, "Pared", wallX - 22, 100, MUTED, 12);
  }
  const sections = state.wall ? [[170, wallX - 14, 1], [wallX + 14, 590, 0.48]] : [[170, 590, 1]];
  sections.forEach(([start, end, scale]) => {
    ctx.strokeStyle = scale === 1 ? BLUE : "#f59e0b";
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    for (let x = start; x <= end; x += 2) {
      const y = 200 + Math.sin((x - start) / 24 - time * 4) * amplitude * scale;
      if (x === start) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  });
  for (let i = 0; i < 5; i += 1) {
    const x = 182 + ((time * 75 + i * 96) % 390);
    if (state.wall && x > wallX - 14 && x < wallX + 14) continue;
    ctx.fillStyle = TEAL;
    ctx.beginPath();
    ctx.arc(x, 200 + Math.sin(x / 24 - time * 4) * amplitude * (state.wall && x > wallX ? 0.48 : 1), 4, 0, Math.PI * 2);
    ctx.fill();
  }
  label(ctx, `${band} GHz  ·  longitud de onda aproximada ${wavelength} cm`, 70, 334, INK, 14);
  label(ctx, state.wall ? "El obstáculo debilita la señal recibida." : "La señal se propaga por el aire hasta el cliente.", 70, 361, state.wall ? AMBER : MUTED, 13);
}

function drawWalls(ctx: CanvasRenderingContext2D, time: number, state: CanvasState) {
  drawGrid(ctx);
  const materialLabel = WALL_MATERIAL_LABELS[state.material];
  const perWallLoss = getWallAttenuation(state.material, state.band);
  const wallCount = state.multipleWalls ? 3 : 1;
  const totalLoss = perWallLoss * wallCount;
  const startX = 82;
  const endX = 680;
  const wallX = 380;
  const amplitude = 31;
  label(ctx, "Cada obstáculo resta energía a la señal recibida", 48, 62, INK, 19);
  roundedBox(ctx, 58, 151, 104, 86, "rgba(59,130,246,.88)");
  label(ctx, "Router", 81, 198, "#0f172a", 15);
  roundedBox(ctx, 600, 151, 104, 86, "rgba(52,211,153,.88)");
  label(ctx, "Cliente", 623, 198, "#0f172a", 15);
  for (let index = 0; index < wallCount; index += 1) {
    const x = state.multipleWalls ? [300, 390, 480][index] : wallX;
    ctx.fillStyle = MATERIAL_COLORS[state.material];
    ctx.fillRect(x - 10, 110, 20, 166);
    label(ctx, state.multipleWalls ? `${materialLabel} ${index + 1}` : materialLabel, x - 30, 100, MUTED, 11);
    const signalBefore = -40 - perWallLoss * index;
    const signalAfter = signalBefore - perWallLoss;
    label(ctx, `Antes ${signalBefore.toFixed(1)} dBm`, x - 44, 264, INK, 9);
    label(ctx, `Después ${signalAfter.toFixed(1)} dBm`, x - 48, 282, MUTED, 9);
  }
  for (let segment = 0; segment <= wallCount; segment += 1) {
    const segmentStart = segment === 0 ? startX : (state.multipleWalls ? [310, 400, 490][segment - 1] : wallX + 10);
    const segmentEnd = segment === wallCount ? endX : (state.multipleWalls ? [290, 380, 470][segment] : wallX - 10);
    const gain = segment === 0 ? 1 : Math.max(0.2, 1 - (perWallLoss / 42) * segment);
    ctx.strokeStyle = segment === 0 ? BLUE : gain > 0.55 ? TEAL : AMBER;
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    for (let x = segmentStart; x <= segmentEnd; x += 2) {
      const y = 194 + Math.sin((x - startX) / 22 - time * 3) * amplitude * gain;
      if (x === segmentStart) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }
  roundedBox(ctx, 166, 294, 428, 58, "rgba(15,23,42,.8)");
  label(ctx, `${state.band} GHz  ·  −${totalLoss} dB en ${wallCount} ${wallCount === 1 ? "pared" : "paredes"}`, 186, 319, AMBER, 15);
  label(ctx, `−${perWallLoss} dB por pared`, 186, 339, MUTED, 12);
  label(ctx, "Niveles de señal ilustrativos; el resultado real depende del entorno.", 72, 372, MUTED, 12);
}

const JOURNEY_STEPS = ["Escucha del canal", "Espera aleatoria", "Transmisión", "Recepción", "ACK recibido"];

function drawDataJourney(ctx: CanvasRenderingContext2D, time: number, state: CanvasState) {
  drawGrid(ctx);
  label(ctx, "Del dispositivo emisor al destino: así viaja un paquete", 48, 57, INK, 19);
  const routerX = 376;
  const clientX = 660;
  const clientCount = Math.max(1, Math.min(state.devices, 6));
  roundedBox(ctx, 50, 150, 116, 90, "rgba(59,130,246,.92)");
  label(ctx, "Emisor", 76, 201, "#0f172a", 16);
  roundedBox(ctx, routerX - 62, 150, 124, 90, "rgba(167,139,250,.92)");
  label(ctx, "Punto de acceso", routerX - 52, 190, "#0f172a", 12);
  label(ctx, "Wi-Fi", routerX - 23, 211, "#0f172a", 11);
  for (let index = 0; index < clientCount; index += 1) {
    const y = 104 + index * (clientCount > 1 ? Math.min(48, 200 / (clientCount - 1)) : 0);
    roundedBox(ctx, clientX - 46, y, 96, 40, index === 0 ? "rgba(52,211,153,.92)" : "rgba(71,85,105,.94)");
    label(ctx, index === 0 ? "Destino" : `Equipo ${index + 1}`, clientX - 34, y + 25, index === 0 ? "#0f172a" : INK, 11);
  }
  ctx.strokeStyle = "rgba(148,163,184,.55)";
  ctx.setLineDash([5, 6]);
  ctx.beginPath();
  ctx.moveTo(166, 195);
  ctx.lineTo(routerX - 62, 195);
  ctx.moveTo(routerX + 62, 195);
  ctx.lineTo(clientX - 46, 124);
  ctx.stroke();
  ctx.setLineDash([]);

  const collision = state.forceCollision && state.sentData;
  const automaticStep = Math.floor(time / 1.4) % JOURNEY_STEPS.length;
  const activeStep = state.stepByStep ? state.journeyStep : automaticStep;
  const hasActiveData = state.sentData;

  if (hasActiveData) {
    if (collision) {
      ctx.strokeStyle = "#fb7185";
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(166, 188);
      ctx.lineTo(routerX - 62, 188);
      ctx.moveTo(166, 202);
      ctx.lineTo(routerX - 62, 202);
      ctx.stroke();
      label(ctx, "¡Colisión!", 222, 174, "#fda4af", 13);
    } else {
      const phase = activeStep <= 1 ? 0 : activeStep === 2 ? 0.5 + ((time * 0.32) % 1) * 0.5 : activeStep >= 3 ? 1 : 0;
      const x = 166 + (routerX - 62 - 166) * phase;
      ctx.fillStyle = AMBER;
      ctx.beginPath();
      ctx.arc(x, 195, 7, 0, Math.PI * 2);
      ctx.fill();
      if (activeStep >= 3) {
        const destinationY = 124;
        const packetX = routerX + 62 + (clientX - 108 - routerX - 62) * ((time * 0.35) % 1);
        ctx.fillStyle = TEAL;
        ctx.beginPath();
        ctx.arc(packetX, 195 + (destinationY - 195) * ((packetX - routerX - 62) / (clientX - 108 - routerX - 62)), 6, 0, Math.PI * 2);
        ctx.fill();
      }
      if (activeStep >= 4) {
        const ackProgress = (time * 0.35) % 1;
        const ackX = clientX - 46 - (clientX - 108 - routerX - 62) * ackProgress;
        const ackY = 124 + (195 - 124) * ackProgress;
        ctx.fillStyle = VIOLET;
        ctx.beginPath();
        ctx.arc(ackX, ackY, 5, 0, Math.PI * 2);
        ctx.fill();
        label(ctx, "ACK ←", 506, 157, VIOLET, 11);
      }
    }
  }

  const stepWidth = 136;
  const stepGap = 9;
  JOURNEY_STEPS.forEach((step, index) => {
    const x = 42 + index * (stepWidth + stepGap);
    const current = index === activeStep && hasActiveData;
    roundedBox(ctx, x, 280, stepWidth, 52, current ? (collision ? "rgba(251,113,133,.2)" : "rgba(96,165,250,.22)") : "rgba(30,41,59,.9)");
    label(ctx, `0${index + 1}`, x + 9, 300, current ? AMBER : MUTED, 10);
    label(ctx, step, x + 9, 320, current ? INK : MUTED, 11);
    if (index < JOURNEY_STEPS.length - 1) {
      label(ctx, "→", x + stepWidth - 1, 310, MUTED, 13);
    }
  });
  label(ctx, `${clientCount} ${clientCount === 1 ? "dispositivo" : "dispositivos"} · ${state.speed === "fast" ? "Rápido" : "Normal"}`, 58, 91, MUTED, 13);
  label(
    ctx,
    !hasActiveData ? "Listo para enviar datos." : collision ? "Colisión forzada: escucha y reintenta con backoff." : `Paso ${activeStep + 1}: ${JOURNEY_STEPS[activeStep]}.`,
    58,
    365,
    collision ? "#fda4af" : INK,
    13,
  );
}

function drawScene(ctx: CanvasRenderingContext2D, scene: WifiLessonScene, time: number, state: CanvasState) {
  ctx.fillStyle = "#0b1220";
  ctx.fillRect(0, 0, WIDTH, HEIGHT);
  switch (scene) {
    case "qam": drawQam(ctx, time, state); break;
    case "ofdm": drawOfdm(ctx, time, state); break;
    case "csma": drawCsma(ctx, time, state); break;
    case "spectrum": drawSpectrum(ctx, time, state); break;
    case "transmission": drawTransmission(ctx, time, state); break;
    case "walls": drawWalls(ctx, time, state); break;
    case "dataJourney": drawDataJourney(ctx, time, state); break;
  }
}

const DESCRIPTIONS: Record<WifiLessonScene, string> = {
  qam: "Diagrama de constelación QAM y una onda modulada. El control cambia el orden de modulación y permite comparar los efectos del ruido.",
  ofdm: "Diagrama animado de portadora única, subportadoras OFDM ortogonales o unidades de recursos OFDMA para varios clientes.",
  csma: "Tres equipos comparten un canal y muestran escucha, espera aleatoria, transmisión y reintento para ilustrar CSMA/CA.",
  spectrum: "Escala visual del espectro electromagnético con las bandas Wi-Fi ubicadas dentro de las microondas.",
  transmission: "Animación de ondas y paquetes de datos que viajan de un router a un cliente, con opciones de banda y obstáculo.",
  walls: "Comparación visual de la amplitud recibida después de atravesar materiales de construcción con distinta pérdida.",
  dataJourney: "Recorrido interactivo de un paquete desde el emisor, por el punto de acceso y el canal Wi-Fi, hasta el equipo de destino; se puede observar la escucha, el backoff, la colisión, la recepción y el acuse.",
};

export function WifiCanvasLesson({
  scene,
  initialBand = "2.4",
  initialMaterial = "concrete",
  showJourneyControls = scene === "dataJourney",
}: {
  scene: WifiLessonScene;
  initialBand?: WifiBand;
  initialMaterial?: WallMaterial;
  showJourneyControls?: boolean;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const elapsedRef = useRef(0);
  const [view, setView] = useState(scene === "qam" ? "1024" : scene === "ofdm" ? "ofdm" : scene === "spectrum" ? "micro" : scene === "transmission" ? "2.4" : "normal");
  const [noise, setNoise] = useState(false);
  const [wall, setWall] = useState(false);
  const [material, setMaterial] = useState<Material>(initialMaterial);
  const [band, setBand] = useState<WifiBand>(initialBand);
  const [multipleWalls, setMultipleWalls] = useState(false);
  const [devices, setDevices] = useState(2);
  const [forceCollision, setForceCollision] = useState(false);
  const [sentData, setSentData] = useState(false);
  const [stepByStep, setStepByStep] = useState(false);
  const [journeyStep, setJourneyStep] = useState(0);
  const [speed, setSpeed] = useState<"normal" | "fast">("normal");
  const [playing, setPlaying] = useState(true);
  const [reducedMotion, setReducedMotion] = useState(false);
  const [canvasError, setCanvasError] = useState(false);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const updatePreference = () => setReducedMotion(media.matches);
    updatePreference();
    media.addEventListener("change", updatePreference);
    return () => media.removeEventListener("change", updatePreference);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) {
      setCanvasError(true);
      return;
    }
    setCanvasError(false);

    let frameId = 0;
    let lastFrame = 0;
    let disposed = false;
    let isInViewport = true;
    let dprMedia: MediaQueryList | null = null;
    let dprListener: (() => void) | null = null;
    const state: CanvasState = {
      view, noise, wall, material, band, multipleWalls,
      devices, forceCollision, sentData, stepByStep, journeyStep, speed,
    };

    const watchDevicePixelRatio = () => {
      if (dprMedia && dprListener) dprMedia.removeEventListener("change", dprListener);
      dprMedia = window.matchMedia(`(resolution: ${window.devicePixelRatio || 1}dppx)`);
      dprListener = () => {
        resize();
        watchDevicePixelRatio();
      };
      dprMedia.addEventListener("change", dprListener);
    };

    const resize = () => {
      if (disposed) return;
      const bounds = canvas.getBoundingClientRect();
      if (!bounds.width) return;
      const ratio = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.round(bounds.width * ratio);
      canvas.height = Math.round((bounds.width * HEIGHT / WIDTH) * ratio);
      context.setTransform(canvas.width / WIDTH, 0, 0, canvas.height / HEIGHT, 0, 0);
      drawScene(context, scene, elapsedRef.current, state);
    };

    const animate = (now: number) => {
      frameId = 0;
      if (disposed) return;
      if (lastFrame) elapsedRef.current += Math.min((now - lastFrame) / 1000, 0.05) * (speed === "fast" ? 2 : 1);
      lastFrame = now;
      drawScene(context, scene, elapsedRef.current, state);
      if (playing && !reducedMotion && isInViewport && !document.hidden) {
        frameId = window.requestAnimationFrame(animate);
      }
    };

    const handleVisibilityChange = () => {
      lastFrame = 0;
      if (document.hidden && frameId) {
        window.cancelAnimationFrame(frameId);
        frameId = 0;
      } else if (!document.hidden && playing && !reducedMotion && isInViewport && !frameId) {
        frameId = window.requestAnimationFrame(animate);
      }
    };
    const intersectionObserver = typeof IntersectionObserver === "undefined"
      ? null
      : new IntersectionObserver(([entry]) => {
          isInViewport = entry.isIntersecting;
          if (!isInViewport && frameId) {
            window.cancelAnimationFrame(frameId);
            frameId = 0;
          } else if (isInViewport && playing && !reducedMotion && !document.hidden && !frameId) {
            frameId = window.requestAnimationFrame(animate);
          }
        });

    const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(resize);
    observer?.observe(canvas);
    intersectionObserver?.observe(canvas);
    window.addEventListener("resize", resize);
    document.addEventListener("visibilitychange", handleVisibilityChange);
    watchDevicePixelRatio();
    resize();
    animate(performance.now());

    return () => {
      disposed = true;
      observer?.disconnect();
      intersectionObserver?.disconnect();
      window.removeEventListener("resize", resize);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      if (dprMedia && dprListener) dprMedia.removeEventListener("change", dprListener);
      window.cancelAnimationFrame(frameId);
    };
  }, [band, devices, forceCollision, journeyStep, material, multipleWalls, noise, playing, reducedMotion, scene, sentData, speed, stepByStep, view, wall]);

  const controlClass = (active: boolean) =>
    `rounded-lg border px-3 py-2 text-sm transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-400 ${
      active ? "border-blue-400 bg-blue-500/20 text-blue-100" : "border-slate-700 bg-slate-900 text-slate-300 hover:border-slate-500"
    }`;
  const button = (text: string, selected: boolean, action: () => void, pressed = selected) => (
    <button type="button" key={text} className={controlClass(selected)} onClick={action} aria-pressed={pressed}>
      {text}
    </button>
  );

  let controls;
  if (scene === "qam") {
    controls = (
      <>
        {[["2", "BPSK · 1 bit"], ["16", "16-QAM · 4 bits"], ["64", "64-QAM · 6 bits"], ["256", "256-QAM · 8 bits"], ["1024", "1024-QAM · 10 bits"]].map(([order, text]) =>
          button(text, view === order, () => setView(order))
        )}
        {button(noise ? "Quitar ruido" : "Añadir ruido", noise, () => setNoise((current) => !current))}
      </>
    );
  } else if (scene === "ofdm") {
    controls = (
      <>
        {button("Portadora única", view === "single", () => setView("single"))}
        {button("OFDM", view === "ofdm" || view === "ofdm-cp", () => setView("ofdm"))}
        {button("OFDMA · Wi-Fi 6", view === "ofdma", () => setView("ofdma"))}
        {view !== "single" && view !== "ofdma" && button("Mostrar prefijo cíclico", view === "ofdm-cp", () => setView(view === "ofdm-cp" ? "ofdm" : "ofdm-cp"))}
      </>
    );
  } else if (scene === "csma") {
    controls = (
      <>
        {button("Acceso coordinado", view !== "collision", () => setView("normal"))}
        {button("Simular colisión", view === "collision", () => setView("collision"))}
      </>
    );
  } else if (scene === "spectrum") {
    controls = (
      <>
        {button("Espectro completo", view === "full", () => setView("full"))}
        {button("Microondas", view === "micro", () => setView("micro"))}
        {button("Bandas Wi-Fi", view === "wifi", () => setView("wifi"))}
        {WIFI_BANDS.map((wifiBand) =>
          button(`Destacar ${wifiBand} GHz`, band === wifiBand, () => setBand(wifiBand))
        )}
      </>
    );
  } else if (scene === "transmission") {
    controls = (
      <>
        {(["2.4", "5", "6"] as const).map((band) => button(`${band} GHz`, view === band, () => setView(band)))}
        {button(wall ? "Quitar obstáculo" : "Agregar obstáculo", wall, () => setWall((current) => !current))}
      </>
    );
  } else if (scene === "walls") {
    controls = (
      <>
        {WIFI_BANDS.map((wifiBand) =>
          button(`${wifiBand} GHz`, band === wifiBand, () => setBand(wifiBand))
        )}
        {(["glass", "drywall", "wood", "brick", "concrete", "metal", "unknown"] as const).map((kind) =>
          button(`${WALL_MATERIAL_LABELS[kind]} −${WALL_ATTENUATION_DB[kind][band]} dB`, material === kind, () => setMaterial(kind))
        )}
        {button(multipleWalls ? "Una pared" : "Tres paredes", multipleWalls, () => setMultipleWalls((current) => !current))}
      </>
    );
  } else {
    const journeyControl = (text: string, selected: boolean, action: () => void, pressed = selected, disabled = false) => (
      <button type="button" key={text} className={controlClass(selected)} onClick={action} aria-pressed={pressed} disabled={disabled}>
        {text}
      </button>
    );
    controls = (
      <>
        {journeyControl("Reiniciar", false, () => {
          elapsedRef.current = 0;
          setDevices(2);
          setForceCollision(false);
          setSentData(false);
          setStepByStep(false);
          setJourneyStep(0);
          setSpeed("normal");
          setPlaying(true);
        })}
        {journeyControl("Añadir dispositivo", false, () => setDevices((count) => Math.min(count + 1, 6)), false, devices >= 6)}
        {journeyControl(forceCollision ? "Quitar colisión" : "Forzar colisión", forceCollision, () => setForceCollision((current) => !current))}
        {journeyControl(sentData ? "Enviar más datos" : "Enviar datos", false, () => {
          setSentData(true);
          setJourneyStep(0);
          elapsedRef.current = 0;
        }, false)}
        {journeyControl(stepByStep ? "Modo automático" : "Paso a paso", stepByStep, () => setStepByStep((current) => !current))}
        {journeyControl("Avanzar paso", false, () => setJourneyStep((current) => (current + 1) % JOURNEY_STEPS.length), false, !stepByStep || !sentData)}
        {journeyControl("Normal", speed === "normal", () => setSpeed("normal"))}
        {journeyControl("Rápido", speed === "fast", () => setSpeed("fast"))}
        <p className="px-2 text-xs text-slate-400" role="status" aria-live="polite">
          {forceCollision && sentData ? "Colisión activada; observa el reintento con backoff." : sentData ? stepByStep ? `Paso ${journeyStep + 1} de ${JOURNEY_STEPS.length}: ${JOURNEY_STEPS[journeyStep]}.` : "Datos en tránsito; el recorrido continúa." : "Prepara el escenario y envía datos para iniciar."}
        </p>
      </>
    );
  }

  return (
    <section className="overflow-hidden rounded-2xl border border-slate-700 bg-slate-950 shadow-2xl" aria-label="Animación interactiva">
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-800 p-3" role="group" aria-label={scene === "dataJourney" ? "Controles del viaje del dato" : "Controles de la animación"}>
        {controls}
        {!(scene === "dataJourney" && showJourneyControls) && (
          <button type="button" className={`${controlClass(false)} ml-auto`} onClick={() => setPlaying((current) => !current)} aria-pressed={!playing}>
            {playing ? "Pausar animación" : "Reanudar animación"}
          </button>
        )}
      </div>
      {canvasError ? (
        <p role="alert" className="p-6 text-sm text-amber-200">
          Este navegador no pudo iniciar el lienzo. {DESCRIPTIONS[scene]}
        </p>
      ) : (
        <canvas
          ref={canvasRef}
          className="block h-auto w-full"
          role="img"
          aria-label={DESCRIPTIONS[scene]}
          aria-describedby={`wifi-canvas-description-${scene}`}
        />
      )}
      {scene === "walls" && (
        <p className="border-t border-slate-800 px-4 py-3 text-sm text-slate-300" role="status" aria-live="polite">
          {WALL_MATERIAL_LABELS[material]} a {band} GHz: {getWallAttenuation(material, band)} dB por pared
          {multipleWalls ? ` · ${getWallAttenuation(material, band) * 3} dB para tres paredes iguales` : ""}.
          {" "}Valores de atenuación utilizados por la planificación Wi-Fi.
        </p>
      )}
      <p id={`wifi-canvas-description-${scene}`} className="sr-only">{DESCRIPTIONS[scene]}</p>
      {reducedMotion && <p className="px-4 pb-2 text-xs text-slate-400">Movimiento reducido: la explicación se muestra estática.</p>}
      <p className="border-t border-slate-800 px-4 py-3 text-xs leading-relaxed text-slate-400">
        La visualización es conceptual: no representa una medición de radio ni sustituye un análisis de cobertura.
      </p>
    </section>
  );
}
