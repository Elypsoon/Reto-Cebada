/** Discover one supplied clip per family without changing the user's filenames. */
import { readdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, extname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const media = join(root, 'public', 'media', 'parcel-videos')
const assignment = JSON.parse(readFileSync(join(media, 'assignment.json'), 'utf8'))
const supported = new Set(['.mp4', '.webm'])
const files = {}
for (const video of assignment.videos) {
  const folder = `${video.video_id}_${video.reference_parcel_id}`
  const candidates = readdirSync(join(media, folder), { withFileTypes: true })
    .filter(entry => entry.isFile() && supported.has(extname(entry.name).toLowerCase()))
    .map(entry => entry.name).sort()
  if (candidates.length > 1) {
    throw new Error(`Hay varios videos en ${folder}. Conserva un solo clip para evitar una asignación ambigua.`)
  }
  if (candidates.length === 1) {
    files[video.video_id] = `/media/parcel-videos/${encodeURIComponent(folder)}/${encodeURIComponent(candidates[0])}`
  }
}
const payload = { schemaVersion: 1, files }
const destination = join(media, 'files.json')
const serialized = JSON.stringify(payload, null, 2) + '\n'
let previous
try { previous = readFileSync(destination, 'utf8') } catch { /* First run. */ }
if (previous !== serialized) writeFileSync(destination, serialized)
console.log(`Medios: ${Object.keys(files).length}/${assignment.videos.length} familias con video; nombres originales conservados.`)
