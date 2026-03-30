export type RecordingState = "idle" | "recording" | "paused" | "stopped";

export class AudioRecorder {
  private mediaRecorder: MediaRecorder | null = null;
  private chunks: Blob[] = [];
  private stream: MediaStream | null = null;
  private _state: RecordingState = "idle";
  private onStateChange?: (state: RecordingState) => void;

  get state(): RecordingState {
    return this._state;
  }

  private setState(s: RecordingState) {
    this._state = s;
    this.onStateChange?.(s);
  }

  async start(onStateChange?: (state: RecordingState) => void): Promise<void> {
    this.onStateChange = onStateChange;
    this.chunks = [];

    this.stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });

    // Prefer webm/opus, fall back to whatever is supported
    const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
      ? "audio/webm;codecs=opus"
      : MediaRecorder.isTypeSupported("audio/webm")
      ? "audio/webm"
      : "";

    this.mediaRecorder = new MediaRecorder(this.stream, mimeType ? { mimeType } : {});
    this.mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) this.chunks.push(e.data);
    };

    this.mediaRecorder.start(1000); // collect chunks every second
    this.setState("recording");
  }

  pause() {
    if (this.mediaRecorder?.state === "recording") {
      this.mediaRecorder.pause();
      this.setState("paused");
    }
  }

  resume() {
    if (this.mediaRecorder?.state === "paused") {
      this.mediaRecorder.resume();
      this.setState("recording");
    }
  }

  stop(): Promise<Blob> {
    return new Promise((resolve) => {
      if (!this.mediaRecorder) {
        resolve(new Blob([]));
        return;
      }

      this.mediaRecorder.onstop = () => {
        const mimeType = this.mediaRecorder?.mimeType || "audio/webm";
        const blob = new Blob(this.chunks, { type: mimeType });
        this.cleanup();
        this.setState("stopped");
        resolve(blob);
      };

      this.mediaRecorder.stop();
    });
  }

  private cleanup() {
    this.stream?.getTracks().forEach((t) => t.stop());
    this.stream = null;
    this.mediaRecorder = null;
  }

  reset() {
    this.cleanup();
    this.chunks = [];
    this.setState("idle");
  }

  static isSupported(): boolean {
    return !!(navigator.mediaDevices?.getUserMedia && typeof MediaRecorder !== "undefined");
  }

  static getExtension(blob: Blob): string {
    if (blob.type.includes("webm")) return ".webm";
    if (blob.type.includes("ogg")) return ".ogg";
    if (blob.type.includes("mp4")) return ".mp4";
    return ".webm";
  }
}
