"use client";

import { useEffect, useState } from "react";
import { api } from "./api";
import type { Persona } from "./types";

/** Lấy persona đầu tiên của user đã lưu ở trang chính (mặc định user 1). */
export function usePersona() {
  const [persona, setPersona] = useState<Persona | null>(null);
  const [userId, setUserId] = useState(1);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let uid = 1;
    try {
      const saved = Number(localStorage.getItem("acs:userId"));
      if (saved > 0) uid = saved;
    } catch {}
    setUserId(uid);
    api.personas(uid).then((l) => setPersona(l[0] ?? null)).catch((e: Error) => setError(e.message));
  }, []);

  return { persona, userId, error };
}
