"use client"

import { useState, useRef, useEffect } from "react"
import { Play, Pause, Volume2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "./button"

interface AudioPlayerProps {
  audioSrc?: string
  className?: string
}

export function AudioPlayer({ audioSrc, className }: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [totalDuration, setTotalDuration] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [volume, setVolume] = useState(1)
  const [isMuted, setIsMuted] = useState(false)
  const [showVolumeSlider, setShowVolumeSlider] = useState(false)

  useEffect(() => {
    const audio = audioRef.current
    if (!audio || !audioSrc) return

    const handleLoadedMetadata = () => {
      setTotalDuration(audio.duration)
      setIsLoading(false)
    }

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime)
    }

    const handleEnded = () => {
      setIsPlaying(false)
      setCurrentTime(0)
    }

    const handleError = () => {
      setIsLoading(false)
      console.error("Error loading audio file")
    }

    audio.addEventListener("loadedmetadata", handleLoadedMetadata)
    audio.addEventListener("timeupdate", handleTimeUpdate)
    audio.addEventListener("ended", handleEnded)
    audio.addEventListener("error", handleError)

    return () => {
      audio.removeEventListener("loadedmetadata", handleLoadedMetadata)
      audio.removeEventListener("timeupdate", handleTimeUpdate)
      audio.removeEventListener("ended", handleEnded)
      audio.removeEventListener("error", handleError)
    }
  }, [audioSrc])

  const handlePlayPause = async () => {
    const audio = audioRef.current
    console.log("Audio Source:", audioRef)
    if (!audio || !audioSrc) return

    if (isPlaying) {
      audio.pause()
      setIsPlaying(false)
    } else {
      try {
        await audio.play()
        setIsPlaying(true)
      } catch (error) {
        console.error("Error playing audio:", error)
      }
    }
  }

  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const audio = audioRef.current
    if (!audio || !audioSrc) return

    const rect = e.currentTarget.getBoundingClientRect()
    const x = e.clientX - rect.left
    const percentage = (x / rect.width) * 100
    const newTime = (percentage / 100) * totalDuration

    audio.currentTime = newTime
    setCurrentTime(newTime)
  }

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current
    if (!audio) return

    const newVolume = parseFloat(e.target.value)
    setVolume(newVolume)
    audio.volume = newVolume

    if (newVolume === 0) {
      setIsMuted(true)
    } else if (isMuted) {
      setIsMuted(false)
    }
  }

  const toggleMute = () => {
    const audio = audioRef.current
    if (!audio) return

    if (isMuted) {
      audio.volume = volume
      setIsMuted(false)
    } else {
      audio.volume = 0
      setIsMuted(true)
    }
  }

  const progress = totalDuration > 0 ? (currentTime / totalDuration) * 100 : 0

  const formatTime = (seconds: number) => {
    if (!isFinite(seconds)) return "0:00"
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, "0")}`
  }

  const displayDuration = totalDuration > 0 ? formatTime(totalDuration) : "0:00"

  return (
    <div className={cn("flex items-center gap-3 p-3 rounded-lg border bg-card", className)}>
      {audioSrc && (
        <audio ref={audioRef} src={audioSrc} preload="metadata" />
      )}

      {/* Play/Pause Button */}
      <Button
        variant="outline"
        size="icon"
        className="h-8 w-8 rounded-full cursor-pointer"
        onClick={handlePlayPause}
        disabled={!audioSrc || isLoading}
      >
        {isPlaying ? (
          <Pause className="h-4 w-4" />
        ) : (
          <Play className="h-4 w-4 ml-0.5" />
        )}
      </Button>

      {/* Progress Bar */}
      <div className="flex-1 space-y-1">
        <div
          className="h-2 bg-muted rounded-full cursor-pointer overflow-hidden"
          onClick={handleProgressClick}
        >
          <div
            className="h-full bg-primary transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>{formatTime(currentTime)}</span>
          <span>{displayDuration}</span>
        </div>
      </div>

      {/* Volume Control */}
      <div
        className="relative"
        onMouseEnter={() => setShowVolumeSlider(true)}
        onMouseLeave={() => setShowVolumeSlider(false)}
      >
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={toggleMute}
        >
          <Volume2 className={cn("h-5 w-5", isMuted && "opacity-50")} />
        </Button>

        {/* Volume Slider - Vertical */}
        {showVolumeSlider && (
          <div className="absolute bottom-full right-0 pb-2">
            <div className="p-3 bg-popover border rounded-md shadow-lg flex flex-col items-center gap-2">
              <div className="text-center text-xs text-muted-foreground">
                {Math.round((isMuted ? 0 : volume) * 100)}%
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={isMuted ? 0 : volume}
                onChange={handleVolumeChange}
                className="h-24 w-2 bg-muted rounded-lg appearance-none cursor-pointer [writing-mode:vertical-lr] [direction:rtl] [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary [&::-moz-range-thumb]:w-3 [&::-moz-range-thumb]:h-3 [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:bg-primary [&::-moz-range-thumb]:border-0"
                style={{
                  background: `linear-gradient(to top, hsl(var(--primary)) 0%, hsl(var(--primary)) ${(isMuted ? 0 : volume) * 100}%, hsl(var(--muted)) ${(isMuted ? 0 : volume) * 100}%, hsl(var(--muted)) 100%)`
                }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
