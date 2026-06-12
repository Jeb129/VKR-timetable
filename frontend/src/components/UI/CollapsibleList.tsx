import React, { useState } from "react";

interface CollapsibleListProps<T> {
  items: T[];
  renderItem: (item: any, index: number) => React.ReactNode;
  collapsedCount?: number;
  containerClassName?: string;
  toggleButtonClassName?: string;
  vertical?: boolean
}

export const CollapsibleList = <T,>({
  items,
  renderItem,
  collapsedCount = 2,
  containerClassName = "",
  toggleButtonClassName = "",
  vertical = true
}: CollapsibleListProps<T>) => {
  const [expanded, setExpanded] = useState(false);

  const displayedItems = expanded ? items : items.slice(0, collapsedCount);
  const hasHidden = items.length > collapsedCount;
  const classname = (vertical ? "flex-col" : "flex-row") + " gap-1 " + containerClassName
  return (
    <>
      <div className={classname}>
        {displayedItems.map((item, index) => renderItem(item, index))}
      </div>

      {hasHidden && (
        <button
          className={toggleButtonClassName}
          onClick={() => setExpanded((prev) => !prev)}
        >
          {expanded ? "Свернуть" : ` ...и ещё ${items.length - collapsedCount}`}
        </button>
      )}
    </>
  );
}