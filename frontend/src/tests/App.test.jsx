import { render, screen, fireEvent } from '@testing-library/react';
import App from '../App';

describe('App Component', () => {
  it('renders the title', () => {
    render(<App />);
    expect(screen.getByText('AutoCleanse Dashboard')).toBeInTheDocument();
  });

  it('renders the start button', () => {
    render(<App />);
    const button = screen.getByRole('button', { name: /Start Mock Analysis/i });
    expect(button).toBeInTheDocument();
  });
});