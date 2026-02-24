/**
 * Local-only chat state: sessions and messages. No API calls.
 * Ready to be wired to backend later (e.g. replace addMessage with API call).
 */
import { create } from "zustand";
import type { Message, Session } from "../types/chat";

function genId(): string {
  return Math.random().toString(36).slice(2, 11);
}

interface ChatState {
  sessions: Session[];
  activeSessionId: string | null;
  messagesBySession: Record<string, Message[]>;

  addSession: () => void;
  setActiveSession: (id: string | null) => void;
  addMessage: (sessionId: string, role: Message["role"], content: string) => void;
  getMessages: (sessionId: string) => Message[];
}

export const useChatStore = create<ChatState>((set, get) => ({
  sessions: [],
  activeSessionId: null,
  messagesBySession: {},

  addSession: () => {
    const session: Session = {
      id: genId(),
      title: "新对话",
      createdAt: Date.now(),
    };
    set((state) => ({
      sessions: [session, ...state.sessions],
      activeSessionId: session.id,
      messagesBySession: { ...state.messagesBySession, [session.id]: [] },
    }));
  },

  setActiveSession: (id) => {
    set({ activeSessionId: id });
  },

  addMessage: (sessionId, role, content) => {
    const message: Message = {
      id: genId(),
      role,
      content,
      timestamp: Date.now(),
    };
    set((state) => ({
      messagesBySession: {
        ...state.messagesBySession,
        [sessionId]: [...(state.messagesBySession[sessionId] ?? []), message],
      },
    }));
  },

  getMessages: (sessionId) => {
    return get().messagesBySession[sessionId] ?? [];
  },
}));
