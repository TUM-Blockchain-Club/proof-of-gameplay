use anchor_lang::prelude::*;
use anchor_spl::token::{self, Mint, Token, TokenAccount, MintTo};
use solana_program::ed25519_program;
use solana_program::instruction::Instruction;
use solana_program::sysvar;

declare_id!("31g5N1BzKGdSJZvHAERYVHLvHFcM7SKU5tsgeTgpTECp");

#[program]
pub mod proof_of_gameplay {
    use super::*;

    pub fn initialize(
    ctx: Context<Initialize>,
) -> Result<()> {
    let state = &mut ctx.accounts.game_state;

    // Initialize values based on Solana blockchain averages
    let base_reward: u64 = 1000;
    let halving_block_count: u64 = 216_000; // Roughly equivalent to one day on the Solana blockchain
    let current_slot = Clock::get()?.slot;  // Get the current slot (will act as the genesis block)

    // Set state
    state.base_reward = base_reward;
    state.genesis_block = current_slot; // Genesis block is the current slot when initialized
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

        // Fixed public key for attestation verification
        let verifier_pubkey = Pubkey::new_from_array([53, 186, 65, 103, 37, 72, 193, 8, 66, 8, 86, 105, 249, 40, 227, 56, 203, 40, 49, 247, 89, 139, 77, 84, 101, 73, 72, 221, 255, 178, 73, 108]);

        // Serialize the score as a message
        let message = score.to_le_bytes();

        // Create an ed25519 signature verification instruction
        let verify_ix = Instruction {
            program_id: ed25519_program::id(),
            accounts: vec![
                AccountMeta::new_readonly(sysvar::instructions::ID, false), // Sysvar instructions
            ],
            data: [
                vec![1], // Verification instruction prefix
                vec![0, 0, 0, 0], // Signature verification count (little endian, 1 signature)
                verifier_pubkey.to_bytes().to_vec(), // Fixed public key (32 bytes)
                vec![message.len() as u8],          // Message length
                message.to_vec(),                   // Message (score as bytes)
                attestation,                        // Signature (64 bytes)
            ]
            .concat(), // Concatenate data
        };

        // Invoke the verification instruction
        solana_program::program::invoke(
            &verify_ix,
            &[
                ctx.accounts.instructions_sysvar.to_account_info(),
            ],
        )?;

        // Determine current epoch
        let current_slot = Clock::get()?.slot;
        let epoch = (current_slot - state.genesis_block) / state.halving_block_count;

        // Update epoch if necessary
        if epoch > state.current_epoch {
            state.previous_best_player = state.current_best_player;
            state.current_epoch = epoch;
            state.current_best_score = 0;
            state.current_best_player = Pubkey::default();
        }

        // Update player state if the new score is better
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
    // Create immutable reference to game_state for the authority
    let game_state_info = ctx.accounts.game_state.to_account_info();

    // Now create a mutable reference to update the state
    let state = &mut ctx.accounts.game_state;

    // Ensure player was the best in the previous epoch
    if ctx.accounts.player.key() != state.previous_best_player {
        return Err(ErrorCode::NotBestPlayer.into());
    }

    // Calculate reward based on the current block slot and halving block count
    let current_slot = Clock::get()?.slot;
    let n = ((current_slot - state.genesis_block) / state.halving_block_count) as u32;
    let reward = state.base_reward >> n; // Equivalent to dividing by 2^n

    // Construct the seeds array for the CPI
    let seeds = &[b"game_state".as_ref(), &[ctx.bumps.game_state]];
    let signer = &[&seeds[..]];

    // Mint tokens to player
    token::mint_to(
        CpiContext::new_with_signer(
            ctx.accounts.token_program.to_account_info(),
            MintTo {
                mint: ctx.accounts.token_mint.to_account_info(),
                to: ctx.accounts.player_token_account.to_account_info(),
                authority: game_state_info, // Use the immutable reference here
            },
            signer,
        ),
        reward,
    )?;

    // Now you can update the state (mutable borrow)
    state.previous_best_player = Pubkey::default();

    Ok(())
}
}

// Account structures and context definitions

#[account]
pub struct GameState {
    pub base_reward: u64,
    pub genesis_block: u64,
    pub halving_block_count: u64,
    pub current_epoch: u64,
    pub current_best_score: u64,
    pub current_best_player: Pubkey,
    pub previous_best_player: Pubkey,
}

impl GameState {
    pub const SIZE: usize = 8 + 8 + 8 + 8 + 8 + 32 + 32;
}

#[account]
pub struct PlayerState {
    pub best_score: u64,
}

impl PlayerState {
    pub const SIZE: usize = 8 + 8;
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
    pub instructions_sysvar: AccountInfo<'info>, // Add this for signature verification
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