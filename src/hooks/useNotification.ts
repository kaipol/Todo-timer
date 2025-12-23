import { useCallback, useEffect, useRef } from 'react';
import { useTodoStore } from '../store/todoStore';
import { TimerMode } from './useTimer';

export interface UseNotificationReturn {
  requestPermission: () => Promise<boolean>;
  showNotification: (mode: TimerMode) => void;
}

export function useNotification(): UseNotificationReturn {
  const settings = useTodoStore((state) => state.settings);
  const notificationsEnabled = settings.notificationsEnabled;
  
  // 缓存权限状态
  const permissionRef = useRef<NotificationPermission>('default');

  useEffect(() => {
    if ('Notification' in window) {
      permissionRef.current = Notification.permission;
    }
  }, []);

  const requestPermission = useCallback(async (): Promise<boolean> => {
    if (!('Notification' in window)) {
      console.warn('This browser does not support notifications');
      return false;
    }

    if (Notification.permission === 'granted') {
      permissionRef.current = 'granted';
      return true;
    }

    if (Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission();
      permissionRef.current = permission;
      return permission === 'granted';
    }

    return false;
  }, []);

  const showNotification = useCallback((mode: TimerMode) => {
    if (!notificationsEnabled) return;
    if (!('Notification' in window)) return;
    if (permissionRef.current !== 'granted') return;

    const titles: Record<TimerMode, string> = {
      work: '工作时间结束！',
      shortBreak: '短休息结束！',
      longBreak: '长休息结束！',
    };

    const bodies: Record<TimerMode, string> = {
      work: '是时候休息一下了 🎉',
      shortBreak: '准备好继续工作了吗？💪',
      longBreak: '休息够了，让我们继续前进！🚀',
    };

    const icons: Record<TimerMode, string> = {
      work: '/icons/work-complete.png',
      shortBreak: '/icons/break-complete.png',
      longBreak: '/icons/break-complete.png',
    };

    try {
      new Notification(titles[mode], {
        body: bodies[mode],
        icon: icons[mode],
        tag: 'timer-notification',
        requireInteraction: false,
      });
    } catch (error) {
      console.warn('Failed to show notification:', error);
    }
  }, [notificationsEnabled]);

  return {
    requestPermission,
    showNotification,
  };
}
