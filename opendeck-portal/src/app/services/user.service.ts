import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { User } from '../models/user.model';

/**
 * User Service
 * Handles user profile operations including profile picture management
 */
@Injectable({
  providedIn: 'root'
})
export class UserService {
  private readonly apiUrl = `${environment.apiBaseUrl}/users`;

  constructor(private http: HttpClient) {}

  /**
   * Upload profile picture
   * @param file - Image file to upload
   * @returns Observable of updated User
   */
  uploadProfilePicture(file: File): Observable<User> {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post<User>(`${this.apiUrl}/me/profile-picture`, formData);
  }

  /**
   * Delete profile picture
   * @returns Observable of updated User
   */
  deleteProfilePicture(): Observable<User> {
    return this.http.delete<User>(`${this.apiUrl}/me/profile-picture`);
  }

  /**
   * Get profile picture URL for a user
   * @param userId - User ID
   * @returns Full URL to profile picture
   */
  getProfilePictureUrl(userId: string): string {
    return `${environment.apiBaseUrl}/users/${userId}/profile-picture`;
  }

  /**
   * Get current user profile
   * @returns Observable of current User
   */
  getCurrentUserProfile(): Observable<User> {
    return this.http.get<User>(`${this.apiUrl}/me`);
  }
}
