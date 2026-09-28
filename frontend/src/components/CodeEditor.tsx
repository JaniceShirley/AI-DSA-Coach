import React from 'react';
import Editor from '@monaco-editor/react';

interface CodeEditorProps {
  code: string;
  onChange: (value: string) => void;
  language?: string;
  theme?: string;
  readOnly?: boolean;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({
  code,
  onChange,
  language = 'python',
  theme = 'vs-dark',
  readOnly = false,
}) => {
  return (
    <div className="w-full h-full min-h-[350px] border border-slate-800 rounded-lg overflow-hidden bg-[#1e1e1e]">
      <Editor
        height="100%"
        defaultLanguage={language}
        language={language}
        theme={theme}
        value={code}
        onChange={(val) => onChange(val || '')}
        options={{
          fontSize: 13,
          fontFamily: "'Fira Code', 'Courier New', monospace",
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          automaticLayout: true,
          readOnly: readOnly,
          tabSize: 4,
          insertSpaces: true,
          lineNumbers: 'on',
          folding: true,
          bracketPairColorization: { enabled: true },
          padding: { top: 12, bottom: 12 },
        }}
      />
    </div>
  );
};
