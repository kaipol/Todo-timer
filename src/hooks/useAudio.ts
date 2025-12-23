import { useRef, useCallback, useEffect } from 'react';
import { useTodoStore } from '../store/todoStore';

export interface UseAudioReturn {
  playNotification: () => void;
  playClick: () => void;
}

export function useAudio(): UseAudioReturn {
  const settings = useTodoStore((state) => state.settings);
  const soundEnabled = settings.soundEnabled;
  const volume = settings.volume;

  // 使用 ref 缓存音频实例，避免重复创建
  const notificationAudioRef = useRef<HTMLAudioElement | null>(null);
  const clickAudioRef = useRef<HTMLAudioElement | null>(null);

  // 初始化音频实例
  useEffect(() => {
    // 创建通知音频
    notificationAudioRef.current = new Audio('/sounds/notification.mp3');
    notificationAudioRef.current.preload = 'auto';
    
    // 创建点击音频
    clickAudioRef.current = new Audio('/sounds/click.mp3');
    clickAudioRef.current.preload = 'auto';

    return () => {
      // 清理音频实例
      if (notificationAudioRef.current) {
        notificationAudioRef.current.pause();
        notificationAudioRef.current = null;
      }
      if (clickAudioRef.current) {
        clickAudioRef.current.pause();
        clickAudioRef.current = null;
      }
    };
  }, []);

  // 更新音量
  useEffect(() => {
    if (notificationAudioRef.current) {
      notificationAudioRef.current.volume = volume;
    }
    if (clickAudioRef.current) {
      clickAudioRef.current.volume = volume;
    }
  }, [volume]);

  const playNotification = useCallback(() => {
    if (!soundEnabled || !notificationAudioRef.current) return;
    
    // 重置播放位置并播放
    notificationAudioRef.current.currentTime = 0;
    notificationAudioRef.current.play().catch((error) => {
      console.warn('Failed to play notification sound:', error);
    });
  }, [soundEnabled]);

  const playClick = useCallback(() => {
    if (!soundEnabled || !clickAudioRef.current) return;
    
    // 重置播放位置并播放
    clickAudioRef.current.currentTime = 0;
    clickAudioRef.current.play().catch((error) => {
      console.warn('Failed to play click sound:', error);
    });
  }, [soundEnabled]);

  return {
    playNotification,
    playClick,
  };
}
