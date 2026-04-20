export const useDraftDnd = ({
  timeslots,
  lessons,
  setLessons,
  setLessonErrors,
  selectedScenarioId
}: any) => {

  const onDragStart = (e: React.DragEvent, lessonId: number) => {
    e.dataTransfer.setData("lessonId", String(lessonId));
  };

  const onDrop = async (e: React.DragEvent, targetTimeslotId: number) => {
    e.preventDefault();
    const lessonId = Number(e.dataTransfer.getData("lessonId"));

    setLessons((prev: any[]) =>
      prev.map(l => l.id === lessonId ? { ...l, timeslot: targetTimeslotId } : l)
    );
  };

  return { onDragStart, onDrop };
};