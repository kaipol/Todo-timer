import { useState, useEffect, useCallback, useRef } from 'react';
import { useTodoStore } from '../store/todoStore';

export type TimerMode = 'work' | 'shortBreak' | 'longBreak';

interface UseTimerOptions {
  onComplete?: (mode: TimerMode) => void;
  onTick?: (timeLeft: number) => void;
}

interface UseTimerReturn {
  timeLeft: number;
  isRunning: boolean;
  mode: TimerMode;
  completedPomodoros: number;
  progress: number;
  start: () => void;
  pause: () => void;
  reset: () => void;
  skip: () => void;
  setMode: (mode: TimerMode) => void;
}

export function useTimer(options: UseTimerOptions = {}): UseTimerReturn {
  const { onComplete, onTick } = options;
  const settings = useTodoStore((state) => state.settings);
  
  // 使用具体的设置值而不是整个 settings 对象
  const workDuration = settings.workDuration;
  const shortBreakDuration = settings.shortBreakDuration;
  const longBreakDuration = settings.longBreakDuration;
  const longBreakInterval = settings.longBreakInterval;
  const autoStartBreaks = settings.autoStartBreaks;
  const autoStartPomodoros = settings.autoStartPomodoros;

  const [mode, setModeState] = useState<TimerMode>('work');
  const [timeLeft, setTimeLeft] = useState(workDuration * 60);
  const [isRunning, setIsRunning] = useState(false);
  const [completedPomodoros, setCompletedPomodoros] = useState(0);

  // 使用 ref 存储回调，避免依赖变化导致的重渲染
  const onCompleteRef = useRef(onComplete);
  const onTickRef = useRef(onTick);
  
  useEffect(() => {
    onCompleteRef.current = onComplete;
    onTickRef.current = onTick;
  }, [onComplete, onTick]);

  // 获取当前模式的总时间
  const getTotalTime = useCallback((currentMode: TimerMode): number => {
    switch (currentMode) {
      case 'work':
        return workDuration * 60;
      case 'shortBreak':
        return shortBreakDuration * 60;
      case 'longBreak':
        return longBreakDuration * 60;
      default:
        return workDuration * 60;
    }
  }, [workDuration, shortBreakDuration, longBreakDuration]);

  // 计算进度百分比
  const progress = ((getTotalTime(mode) - timeLeft) / getTotalTime(mode)) * 100;

  // 设置模式
  const setMode = useCallback((newMode: TimerMode) => {
    setModeState(newMode);
    setTimeLeft(getTotalTime(newMode));
    setIsRunning(false);
  }, [getTotalTime]);

  // 处理计时器完成
  const handleComplete = useCallback(() => {
    const currentMode = mode;
    
    if (currentMode === 'work') {
      const newCompletedPomodoros = completedPomodoros + 1;
      setCompletedPomodoros(newCompletedPomodoros);
      
      // 判断是否需要长休息
      if (newCompletedPomodoros % longBreakInterval === 0) {
        setModeState('longBreak');
        setTimeLeft(longBreakDuration * 60);
        if (autoStartBreaks) {
          setIsRunning(true);
        } else {
          setIsRunning(false);
        }
      } else {
        setModeState('shortBreak');
        setTimeLeft(shortBreakDuration * 60);
        if (autoStartBreaks) {
          setIsRunning(true);
        } else {
          setIsRunning(false);
        }
      }
    } else {
      // 休息结束，开始工作
      setModeState('work');
      setTimeLeft(workDuration * 60);
      if (autoStartPomodoros) {
        setIsRunning(true);
      } else {
        setIsRunning(false);
      }
    }

    onCompleteRef.current?.(currentMode);
  }, [
    mode,
    completedPomodoros,
    longBreakInterval,
    longBreakDuration,
    shortBreakDuration,
    workDuration,
    autoStartBreaks,
    autoStartPomodoros,
  ]);

  // 计时器核心逻辑
  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;

    if (isRunning && timeLeft > 0) {
      intervalId = setInterval(() => {
        setTimeLeft((prev) => {
          const newTime = prev - 1;
          onTickRef.current?.(newTime);
          return newTime;
        });
      }, 1000);
    } else if (isRunning && timeLeft === 0) {
      handleComplete();
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [isRunning, timeLeft, handleComplete]);

  // 当设置改变时更新时间（仅在未运行时）
  useEffect(() => {
    if (!isRunning) {
      setTimeLeft(getTotalTime(mode));
    }
  }, [workDuration, shortBreakDuration, longBreakDuration, mode, isRunning, getTotalTime]);

  const start = useCallback(() => {
    setIsRunning(true);
  }, []);

  const pause = useCallback(() => {
    setIsRunning(false);
  }, []);

  const reset = useCallback(() => {
    setIsRunning(false);
    setTimeLeft(getTotalTime(mode));
  }, [mode, getTotalTime]);

  const skip = useCallback(() => {
    handleComplete();
  }, [handleComplete]);

  return {
    timeLeft,
    isRunning,
    mode,
    completedPomodoros,
    progress,
    start,
    pause,
    reset,
    skip,
    setMode,
  };
}
