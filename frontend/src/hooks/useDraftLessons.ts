import { useEffect, useState } from "react";

export const useDraftLessons = (scenarioId: any, targetId: any, filterType: any) => {
  const [lessons, setLessons] = useState<any[]>([]);
  const [lessonErrors, setLessonErrors] = useState<any[]>([]);
  const [isChecking, setIsChecking] = useState(false);

  useEffect(() => {
    const load = async () => {
      if (!scenarioId || !targetId) return;
      setLessons([]);
    };
    load();
  }, [scenarioId, targetId, filterType]);

  return {
    lessons,
    setLessons,
    lessonErrors,
    setLessonErrors,
    isChecking
  };
};