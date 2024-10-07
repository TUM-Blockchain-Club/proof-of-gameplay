use anchor_lang::prelude::*;
use anchor_spl::token::{self, Mint, Token, TokenAccount, MintTo};
use ed25519_dalek::{PublicKey, Signature, Verifier};

declare_id!("58aRQ8LWqsrnxgWY77b6DZmT4pxWF17cazq9eG1eU7br");

#[program]
pub mod proof_of_gameplay {
    use super::*;

    pub fn initialize(
        ctx: Context<Initialize>,
        base_reward: u64,
        genesis_block: u64,
        halving_block_count: u64,
        operator: Pubkey,
    ) -> Result<()> {
        let state = &mut ctx.accounts.game_state;
        state.operator = operator;
        state.base_reward = base_reward;
        state.genesis_block = genesis_block;
        state.halving_block_count = halving_block_count;
        state.current_epoch = 0;
        state.current_best_score = 0;
        state.current_best_player = Pubkey::default();
        state.previous_best_player = Pubkey::default();
        Ok(())
    }

    pub fn submit_gameplay(
        ctx: Context<SubmitGameplay>,
        score: u64,
        attestation: Vec<u8>,
    ) -> Result<()> {
        let state = &mut ctx.accounts.game_state;
        let player = &ctx.accounts.player;
        let player_state = &mut ctx.accounts.player_state;

        // Convert Pubkey to ed25519 PublicKey
        let operator_pubkey_bytes = state.operator.to_bytes();
        let operator_pubkey = PublicKey::from_bytes(&operator_pubkey_bytes).map_err(|_| {
            msg!("Invalid operator public key.");
            ErrorCode::InvalidAttestation
        })?;
    
        // Verify attestation signature (operator signed the player's score)
        let message = score.to_le_bytes();
        let signature = Signature::from_bytes(&attestation).map_err(|_| {
            msg!("Invalid attestation signature.");
            ErrorCode::InvalidAttestation
        })?;
    
        operator_pubkey.verify(&message, &signature).map_err(|_| {
            msg!("Signature verification failed.");
            ErrorCode::InvalidAttestation
        })?;

        // Determine current epoch
        let current_slot = Clock::get()?.slot;
        let epoch = (current_slot - state.genesis_block) / state.halving_block_count;

        // Update epoch if necessary
        if epoch > state.current_epoch {
            // Move to next epoch
            state.previous_best_player = state.current_best_player;
            state.current_epoch = epoch;
            state.current_best_score = 0;
            state.current_best_player = Pubkey::default();
            // PlayerState accounts will be re-initialized in new epoch
        }

        // Check if player's new score is better than their previous in this epoch
        if score > player_state.best_score {
            player_state.best_score = score;
        } else {
            return Err(ErrorCode::ScoreNotBetter.into());
        }

        // Check if player's score is better than current best
        if score > state.current_best_score {
            state.current_best_score = score;
            state.current_best_player = player.key();
        }

        Ok(())
    }

    pub fn claim_rewards(ctx: Context<ClaimRewards>) -> Result<()> {
        // Create immutable reference to game_state first for the authority
        let game_state_info = ctx.accounts.game_state.to_account_info();
        
        // Use the bump directly from the context and structure the seeds array correctly
        let bump = ctx.bumps.game_state;
        let seeds = &[b"game_state".as_ref(), &[bump]];
        let signer = &[&seeds[..]];
    
        // Now do mutable borrow
        let state = &mut ctx.accounts.game_state;
        let player = &ctx.accounts.player;
        let token_mint = &ctx.accounts.token_mint;
        let player_token_account = &ctx.accounts.player_token_account;
        let token_program = &ctx.accounts.token_program;
    
        // Ensure player was best in previous epoch
        if player.key() != state.previous_best_player {
            return Err(ErrorCode::NotBestPlayer.into());
        }
    
        // Calculate reward
        let current_slot = Clock::get()?.slot;
        let n = ((current_slot - state.genesis_block) / state.halving_block_count) as u32;
        let reward = state.base_reward >> n; // Equivalent to dividing by 2^n
    
        // Mint tokens to player
        token::mint_to(
            CpiContext::new_with_signer(
                token_program.to_account_info(),
                MintTo {
                    mint: token_mint.to_account_info(),
                    to: player_token_account.to_account_info(),
                    authority: game_state_info, // Immutable borrow here
                },
                signer,
            ),
            reward,
        )?;
    
        // Reset previous best player to prevent multiple claims
        state.previous_best_player = Pubkey::default();
    
        Ok(())
    }      
         
}

// Account structures and context definitions

#[account]
pub struct GameState {
    pub operator: Pubkey,
    pub base_reward: u64,
    pub genesis_block: u64,
    pub halving_block_count: u64,
    pub current_epoch: u64,
    pub current_best_score: u64,
    pub current_best_player: Pubkey,
    pub previous_best_player: Pubkey,
}

impl GameState {
    pub const SIZE: usize = 8  // Discriminator
        + 32  // operator
        + 8   // base_reward
        + 8   // genesis_block
        + 8   // halving_block_count
        + 8   // current_epoch
        + 8   // current_best_score
        + 32  // current_best_player
        + 32; // previous_best_player
}

#[account]
pub struct PlayerState {
    pub best_score: u64,
}

impl PlayerState {
    pub const SIZE: usize = 8  // Discriminator
        + 8; // best_score
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(
        init,
        payer = payer,
        space = GameState::SIZE,
        seeds = [b"game_state"],
        bump
    )]
    pub game_state: Account<'info, GameState>,
    #[account(mut)]
    pub payer: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct SubmitGameplay<'info> {
    #[account(
        mut,
        seeds = [b"game_state"],
        bump
    )]
    pub game_state: Account<'info, GameState>,
    #[account(
        init_if_needed,
        payer = player,
        space = PlayerState::SIZE,
        seeds = [
            b"player_state",
            player.key().as_ref(),
            &game_state.current_epoch.to_le_bytes()
        ],
        bump
    )]
    pub player_state: Account<'info, PlayerState>,
    #[account(mut)]
    pub player: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct ClaimRewards<'info> {
    #[account(
        mut,
        seeds = [b"game_state"],
        bump
    )]
    pub game_state: Account<'info, GameState>,
    #[account(mut)]
    pub player: Signer<'info>,
    #[account(mut)]
    pub token_mint: Account<'info, Mint>,
    #[account(mut)]
    pub player_token_account: Account<'info, TokenAccount>,
    pub token_program: Program<'info, Token>,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Invalid attestation signature.")]
    InvalidAttestation,
    #[msg("Submitted score is not better than previous score.")]
    ScoreNotBetter,
    #[msg("Player was not the best in the previous epoch.")]
    NotBestPlayer,
}
