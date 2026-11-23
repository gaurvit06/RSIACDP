# Casework frontend design

The public home and the investigation workspace use a single centered frame. The wordmark stays in the same place when you enter the workspace. A breadcrumb identifies the current investigation view, and workspace navigation sits below the full-width header. The shared page header places the title, explanation and main action together. Summary cards, guide cards and evidence records follow a common border and spacing scale.

## Template reference

The layout draws on Tabler’s free, MIT-licensed boxed dashboard. Its bounded page, common top bar, page headers with actions and responsive card grid informed the layout. Casework uses its own React components, CSS, icons and data. CoreUI Free React was also considered. [Tabler boxed dashboard](https://preview.tabler.io/layout-boxed.html) · [Tabler source and license](https://github.com/tabler/tabler) · [CoreUI Free React](https://github.com/coreui/coreui-free-react-admin-template)

## Palette and hierarchy

| Role | Color | Use |
| --- | --- | --- |
| White | `#FFFFFF` | Canvas, case records and dialog surfaces |
| Storm Green | `#0F282F` | Headings, body text, logo background and primary button labels |
| Vivid Cyan | `#02EFF0` | Primary button fills, fingerprint mark and source accents |
| Brand gradient | `#0F282F` to `#02EFF0` | Shared outer frame |
| Pale cyan | `#D9F7F7` | Selected navigation, chips and route header tint |
| Dark teal | `#075C63` | Links and accent text on light surfaces |
| Teal | `#00747A` | Keyboard focus |

Use short, sentence-case headings, rounded action buttons and light dividers. Keep model and evidence labels readable independently of color. Green indicates lower risk or source support for a specific claim, red indicates model risk or concern, amber indicates uncertainty and gray indicates a neutral outcome.

## Responsive behavior

The case queue uses a table on desktop and labelled records on phones. The sidebar collapses on desktop and opens as a drawer on mobile. Keep horizontal scrolling inside data tables when individual records cannot reflow. Use the system reduced-motion preference for decorative transitions.

## Implementation

SiteFrame.tsx provides the shared frame and route headers, with layout styles in `frontend/src/site-frame.css`. Shared tokens, controls and responsive navigation are in `frontend/src/workspace-theme.css`. The public dashboard, case reading view and evidence workspace use those tokens in their component styles. The shared wordmark is in `frontend/src/CaseworkBrand.tsx`. The Inter font license is in `frontend/public/fonts/inter/OFL.txt`.
