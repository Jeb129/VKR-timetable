import { useEffect, useState } from "react";

export const useInitialRefs = () => {
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [timeslots, setTimeslots] = useState<any[]>([]);
  const [groups, setGroups] = useState<any[]>([]);
  const [teachers, setTeachers] = useState<any[]>([]);

  useEffect(() => {
    const load = async () => {
      // заменить на реальные сервисы
      setScenarios([]);
      setTimeslots([]);
      setGroups([]);
      setTeachers([]);
    };
    load();
  }, []);

  return { scenarios, timeslots, groups, teachers };
};