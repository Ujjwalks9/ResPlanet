import axios from 'axios';

const API_URL = 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const endpoints = {
  auth: {
    google: '/auth/login/google',
  },
  feed: {
    main: '/feed',
    trending: '/feed/trending',
  },
  projects: {
    upload: '/upload',
    details: (id: string) => `/projects/${id}`,
    file: (id: string) => `${API_URL}/projects/${id}/file`,
    review: (id: string) => `/projects/${id}/review`,
  },
  collab: {
    request: '/collab/request',
    myRequests: (userId: string) => `/collab/requests/${userId}`,
    update: (id: string, status: string) => `/collab/${id}/${status}`,
  },
  chat: {
    ws: (projectId: string, userId: string) => `ws://localhost:8000/ws/chat/${projectId}/${userId}`,
  }
};