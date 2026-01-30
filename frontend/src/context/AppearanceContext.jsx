// src/context/AppearanceContext.jsx
import { createContext, useContext, useState } from 'react';

const AppearanceContext = createContext();

export function AppearanceProvider({ children }) {
  const [fontSize, setFontSize] = useState("medium");
  const [lineSpacing, setLineSpacing] = useState("normal");
  const [autoScrollEnabled, setAutoScrollEnabled] = useState(true);

  return (
    <AppearanceContext.Provider 
      value={{ 
        fontSize, setFontSize,
        lineSpacing, setLineSpacing,
        autoScrollEnabled, setAutoScrollEnabled 
      }}
    >
      {children}
    </AppearanceContext.Provider>
  );
}

export const useAppearance = () => useContext(AppearanceContext);