/**
 * Low-Latency 16kHz Linear PCM AudioWorklet Processor.
 * Runs on a dedicated Web Audio thread.
 * Downsamples native browser microphone audio to 16,000 Hz 16-bit Linear PCM (Int16Array)
 * and emits 100ms chunks (ArrayBuffer) to the main thread via postMessage.
 */

class PCMRecorderProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.bufferSize = 1600; // 100ms at 16kHz
    this.outputBuffer = new Int16Array(this.bufferSize);
    this.outputIndex = 0;
    this.resampleRatio = sampleRate / 16000;
    this.resampleAccumulator = 0;
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (!input || input.length === 0) {
      return true;
    }

    const channelData = input[0]; // Mono channel
    if (!channelData) {
      return true;
    }

    for (let i = 0; i < channelData.length; i++) {
      this.resampleAccumulator += 1;
      if (this.resampleAccumulator >= this.resampleRatio) {
        this.resampleAccumulator -= this.resampleRatio;

        // Clamp float sample (-1.0 to 1.0) and convert to 16-bit signed integer
        const s = Math.max(-1, Math.min(1, channelData[i]));
        const val = s < 0 ? s * 0x8000 : s * 0x7fff;
        this.outputBuffer[this.outputIndex++] = Math.round(val);

        if (this.outputIndex >= this.bufferSize) {
          // Emit 100ms PCM chunk to main thread
          this.port.postMessage(this.outputBuffer.buffer, [this.outputBuffer.buffer]);
          this.outputBuffer = new Int16Array(this.bufferSize);
          this.outputIndex = 0;
        }
      }
    }

    return true;
  }
}

registerProcessor("pcm-recorder-processor", PCMRecorderProcessor);
