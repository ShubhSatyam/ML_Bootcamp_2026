const SUPPORTED_EXTENSIONS = [".wav", ".mp3", ".m4a", ".mp4", ".ogg", ".flac", ".webm"];

export function validateAudio(file: File, maxSizeMb: number): string | null {
  if (file.size === 0) return "This file is empty. Choose a recording with audio.";
  const extension = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
  if (!SUPPORTED_EXTENSIONS.includes(extension)) {
    return "Unsupported format. Choose a WAV, MP3, M4A, MP4, OGG, FLAC, or WebM file.";
  }
  if (file.size > maxSizeMb * 1024 * 1024) {
    return `This file is larger than the ${maxSizeMb} MB upload limit.`;
  }
  return null;
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
