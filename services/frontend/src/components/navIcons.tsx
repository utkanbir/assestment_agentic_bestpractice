import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

const base = { width: 18, height: 18, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 2, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };

export function IconHome(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M3 9.5 12 3l9 6.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1V9.5z" />
    </svg>
  );
}

export function IconMic(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <rect x="9" y="2" width="6" height="11" rx="3" />
      <path d="M5 10a7 7 0 0 0 14 0M12 17v4" />
    </svg>
  );
}

export function IconList(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" />
    </svg>
  );
}

export function IconBot(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <rect x="4" y="8" width="16" height="10" rx="2" />
      <path d="M12 2v4M8 12h.01M16 12h.01M9 16h6" />
    </svg>
  );
}

export function IconLayers(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="m12 2 8 4.5v7L12 18l-8-4.5v-7L12 2z" />
      <path d="m12 12 8-4.5M12 12 4 7.5M12 12v6" />
    </svg>
  );
}

export function IconShare(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="18" cy="5" r="3" />
      <circle cx="6" cy="12" r="3" />
      <circle cx="18" cy="19" r="3" />
      <path d="m8.6 13.5 6.8 3.9M15.4 6.6 8.6 10.5" />
    </svg>
  );
}

export function IconGraph(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="5" cy="12" r="2" />
      <circle cx="12" cy="5" r="2" />
      <circle cx="19" cy="15" r="2" />
      <path d="M7 11.5 10.5 7M13.5 7 17 13.5" />
    </svg>
  );
}

export function IconFlow(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M6 6h4v4H6zM14 14h4v4h-4z" />
      <path d="M10 8h4M12 12v2" />
    </svg>
  );
}

export function IconClipboard(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2" />
      <rect x="9" y="3" width="6" height="4" rx="1" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  );
}

export function IconFlame(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M12 22c4-3 6-6.5 6-10a6 6 0 0 0-11-3 6 6 0 0 0-11 3c0 3.5 2 7 6 10z" />
    </svg>
  );
}

export function IconChart(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M3 3v18h18" />
      <path d="M7 16V9M12 16V5M17 16v-4" />
    </svg>
  );
}

export function IconBriefcase(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <rect x="2" y="7" width="20" height="14" rx="2" />
      <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" />
    </svg>
  );
}

export function IconMap(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M3 6l6-2 6 2 6-2v14l-6 2-6-2-6 2V6z" />
      <path d="M9 4v14M15 6v14" />
    </svg>
  );
}

export function IconDocument(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <path d="M14 2v6h6M8 13h8M8 17h5" />
    </svg>
  );
}

export function IconMessage(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M21 11.5a8.4 8.4 0 0 1-1.9 5.4 8.5 8.5 0 0 1-6.6 3 8.4 8.4 0 0 1-3.9-1L3 20l1.9-5.6A8.4 8.4 0 0 1 3 11.5 8.5 8.5 0 0 1 11.5 3 8.5 8.5 0 0 1 21 11.5z" />
    </svg>
  );
}

export function IconStack(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M12 2 2 7l10 5 10-5-10-5z" />
      <path d="m2 17 10 5 10-5M2 12l10 5 10-5" />
    </svg>
  );
}

export function IconUsers(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}

export const NAV_ICONS = {
  home: IconHome,
  mic: IconMic,
  list: IconList,
  bot: IconBot,
  layers: IconLayers,
  stack: IconStack,
  share: IconShare,
  graph: IconGraph,
  flow: IconFlow,
  clipboard: IconClipboard,
  flame: IconFlame,
  chart: IconChart,
  briefcase: IconBriefcase,
  map: IconMap,
  document: IconDocument,
  message: IconMessage,
  users: IconUsers,
} as const;

export type NavIconName = keyof typeof NAV_ICONS;
