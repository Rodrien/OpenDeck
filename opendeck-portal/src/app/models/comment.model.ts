/**
 * Vote Type
 * Represents the type of vote on a comment
 */
export type VoteType = 'upvote' | 'downvote';

/**
 * User Info
 * Minimal user information for comment author
 */
export interface UserInfo {
  id: string;
  name: string;
  email: string;
}

/**
 * Deck Comment Model
 * Represents a comment on a deck
 */
export interface DeckComment {
  id: string;
  deck_id: string;
  user_id: string;
  user?: UserInfo;
  content: string;
  parent_comment_id: string | null;
  is_edited: boolean;
  upvotes: number;
  downvotes: number;
  score: number;
  user_vote: VoteType | null;
  created_at: string;
  updated_at: string;
}

/**
 * Create Comment DTO
 * Used when creating a new comment
 */
export interface CreateCommentDto {
  content: string;
  parent_comment_id?: string | null;
}

/**
 * Update Comment DTO
 * Used when updating an existing comment
 */
export interface UpdateCommentDto {
  content: string;
}

/**
 * Vote Create DTO
 * Used when voting on a comment
 */
export interface VoteCreateDto {
  vote_type: VoteType;
}

/**
 * Vote Counts Response
 * Response from voting on a comment
 */
export interface VoteCountsResponse {
  comment_id: string;
  upvotes: number;
  downvotes: number;
  score: number;
  user_vote: VoteType | null;
}

/**
 * Comment List Response
 * Paginated list of comments
 */
export interface CommentListResponse {
  items: DeckComment[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * Comment Filter Params
 * Query parameters for filtering comments
 */
export interface CommentFilterParams {
  limit?: number;
  offset?: number;
}
