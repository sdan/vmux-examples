"use client";

import { useEffect, useRef, useState } from "react";
import type { ChangeEvent } from "react";

type VideoState = {
  isPlaying: boolean;
  isMuted: boolean;
  isLoading: boolean;
  currentTime: number;
  duration: number;
  volume: number;
};

export default function VideoPage() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [state, setState] = useState<VideoState>({
    isPlaying: false,
    isMuted: false,
    isLoading: true,
    currentTime: 0,
    duration: 0,
    volume: 1,
  });

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const onLoaded = () => setState((prev) => ({ ...prev, duration: video.duration, isLoading: false }));
    const onTimeUpdate = () => setState((prev) => ({ ...prev, currentTime: video.currentTime }));
    const onPlay = () => setState((prev) => ({ ...prev, isPlaying: true }));
    const onPause = () => setState((prev) => ({ ...prev, isPlaying: false }));
    const onVolumeChange = () => setState((prev) => ({ ...prev, volume: video.volume, isMuted: video.muted }));

    video.addEventListener("loadedmetadata", onLoaded);
    video.addEventListener("timeupdate", onTimeUpdate);
    video.addEventListener("play", onPlay);
    video.addEventListener("pause", onPause);
    video.addEventListener("volumechange", onVolumeChange);

    onVolumeChange();
    return () => {
      video.removeEventListener("loadedmetadata", onLoaded);
      video.removeEventListener("timeupdate", onTimeUpdate);
      video.removeEventListener("play", onPlay);
      video.removeEventListener("pause", onPause);
      video.removeEventListener("volumechange", onVolumeChange);
    };
  }, []);

  const formatTime = (value: number) => {
    if (!Number.isFinite(value) || value < 0) return "0:00";
    const total = Math.floor(value);
    const minutes = Math.floor(total / 60);
    const seconds = String(total % 60).padStart(2, "0");
    return `${minutes}:${seconds}`;
  };

  const togglePlay = () => {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused) {
      void video.play();
    } else {
      video.pause();
    }
  };

  const handleSeek = (event: ChangeEvent<HTMLInputElement>) => {
    const video = videoRef.current;
    if (!video) return;
    const next = Number(event.currentTarget.value);
    video.currentTime = Number.isFinite(next) ? next : 0;
  };

  const handleVolume = (event: ChangeEvent<HTMLInputElement>) => {
    const video = videoRef.current;
    if (!video) return;
    const next = Number(event.currentTarget.value);
    video.volume = next;
    video.muted = next === 0;
  };

  const toggleMute = () => {
    const video = videoRef.current;
    if (!video) return;
    video.muted = !video.muted;
  };

  return (
    <main className="video-shell">
      <section className="video-card">
        <h1>vmux Video Player Demo</h1>
        <p>Custom HTML5 controls + local MP4 from <code>llm-chat/public/videos</code>.</p>

        <div className="player-wrap">
          <video
            ref={videoRef}
            preload="metadata"
            className="video"
            onContextMenu={(event) => event.preventDefault()}
          >
            <source src="/videos/vmux-demo.mp4" type="video/mp4" />
          </video>
        </div>

        <div className="toolbar">
          <button onClick={togglePlay} type="button">
            {state.isPlaying ? "Pause" : "Play"}
          </button>
          <button onClick={toggleMute} type="button">
            {state.isMuted ? "Unmute" : "Mute"}
          </button>
          <span>
            {formatTime(state.currentTime)} / {formatTime(state.duration)}
          </span>
          <span className="status">
            {state.isLoading ? "Loading metadata..." : "Ready"}
          </span>
        </div>

        <label className="slider-label">
          Seek
          <input
            type="range"
            min={0}
            max={state.duration || 0}
            step={0.1}
            value={state.currentTime}
            onChange={handleSeek}
            disabled={state.duration === 0}
          />
        </label>

        <label className="slider-label">
          Volume
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={state.volume}
            onChange={handleVolume}
          />
        </label>
      </section>

      <style jsx>{`
        .video-shell {
          min-height: 100vh;
          display: grid;
          place-items: center;
          padding: 2rem;
          background: #080b16;
          color: #ecf2ff;
        }
        .video-card {
          width: min(920px, 100%);
          border-radius: 14px;
          padding: 1.2rem;
          background: #11172d;
          border: 1px solid #334155;
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
        }
        .player-wrap {
          border-radius: 12px;
          overflow: hidden;
          background: #000;
        }
        .video {
          width: 100%;
          aspect-ratio: 16 / 9;
          background: #000;
          display: block;
        }
        h1 {
          margin: 0 0 0.5rem;
          font-size: 1.5rem;
        }
        p {
          margin: 0 0 1rem;
          color: #96a2bf;
        }
        .toolbar {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          margin: 0.9rem 0 0.6rem;
          flex-wrap: wrap;
        }
        button {
          background: #4f46e5;
          color: white;
          border: none;
          padding: 0.5rem 0.85rem;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 600;
        }
        .status {
          font-size: 0.9rem;
          margin-left: auto;
          color: #cbd5e1;
        }
        .slider-label {
          display: grid;
          font-size: 0.85rem;
          gap: 0.4rem;
          margin: 0.7rem 0;
          color: #dbeafe;
        }
        input[type="range"] {
          width: 100%;
        }
      `}</style>
    </main>
  );
}
