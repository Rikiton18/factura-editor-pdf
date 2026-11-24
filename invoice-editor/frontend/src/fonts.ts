// Fonts the editor can draw an edit in. They are the base-14 PDF fonts the server
// exports with, so what the page shows is what the exported PDF contains.
export const FONT_CHOICES = [
  { name: 'Helvetica', label: 'Helvetica' },
  { name: 'Helvetica-Bold', label: 'Helvetica negrita' },
  { name: 'Courier', label: 'Courier' },
  { name: 'Courier-Bold', label: 'Courier negrita' },
] as const

export type FontName = (typeof FONT_CHOICES)[number]['name']

const HELVETICA_STACK = 'Helvetica, Arial, "Liberation Sans", sans-serif'
const COURIER_STACK = '"Courier New", Courier, "Liberation Mono", monospace'

/**
 * CSS for a font name from the server. Anything that is not Courier or one of the
 * bold choices shows as regular Helvetica, which is also how the exporter draws it.
 */
export function cssFont(fontName: string): { fontFamily: string; fontWeight: 400 | 700 } {
  return {
    fontFamily: fontName.startsWith('Courier') ? COURIER_STACK : HELVETICA_STACK,
    fontWeight: fontName === 'Helvetica-Bold' || fontName === 'Courier-Bold' ? 700 : 400,
  }
}
