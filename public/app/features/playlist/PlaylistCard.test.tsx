import { render, screen } from '@testing-library/react';
import { TestProvider } from 'test/helpers/TestProvider';

import { contextSrv } from 'app/core/services/context_srv';

import { type Playlist, type PlaylistSpec } from '../../api/clients/playlist/v1';

import { PlaylistCard } from './PlaylistCard';

function getPlaylist(annotations?: Record<string, string>, spec?: Partial<PlaylistSpec>): Playlist {
  return {
    apiVersion: 'playlist.grafana.app/v1',
    kind: 'Playlist',
    metadata: {
      name: 'foo',
      ...(annotations ? { annotations } : {}),
    },
    spec: {
      title: 'Test Playlist',
      interval: '5m',
      items: [],
      ...spec,
    },
  };
}

function setup(playlist: Playlist) {
  jest.spyOn(contextSrv, 'hasPermission').mockReturnValue(true);
  return render(
    <TestProvider>
      <PlaylistCard playlist={playlist} setStartPlaylist={jest.fn()} setPlaylistToDelete={jest.fn()} />
    </TestProvider>
  );
}

describe('PlaylistCard', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('does not render the provisioned badge for an unmanaged playlist', () => {
    setup(getPlaylist());

    expect(screen.getByText('Test Playlist')).toBeInTheDocument();
    expect(screen.queryByTestId('icon-exchange-alt')).not.toBeInTheDocument();
  });

  it('renders the provisioned badge for a managed playlist', () => {
    setup(
      getPlaylist({
        'grafana.app/managedBy': 'repo',
        'grafana.app/managerId': 'foo-repo',
      })
    );

    expect(screen.getByText('Test Playlist')).toBeInTheDocument();
    expect(screen.getByText('5m')).toBeInTheDocument();
    expect(screen.getByTestId('icon-exchange-alt')).toBeInTheDocument();
  });

  it('shows the stored interval and zero items for an empty playlist', () => {
    setup(getPlaylist());

    expect(screen.getByText('5m')).toBeInTheDocument();
    expect(screen.getByText('0 items')).toBeInTheDocument();
  });

  it('uses the singular item label for one item', () => {
    setup(
      getPlaylist(undefined, {
        items: [{ type: 'dashboard_by_uid', value: 'abc' }],
      })
    );

    expect(screen.getByText('1 item')).toBeInTheDocument();
    expect(screen.queryByText('1 items')).not.toBeInTheDocument();
  });

  it('uses the plural item label for many items', () => {
    setup(
      getPlaylist(undefined, {
        interval: '10s',
        items: [
          { type: 'dashboard_by_uid', value: 'a' },
          { type: 'dashboard_by_uid', value: 'b' },
          { type: 'dashboard_by_tag', value: 'prod' },
        ],
      })
    );

    expect(screen.getByText('10s')).toBeInTheDocument();
    expect(screen.getByText('3 items')).toBeInTheDocument();
  });

  it('shows zero items when the items list is missing', () => {
    const playlist = getPlaylist();
    delete (playlist.spec as { items?: PlaylistSpec['items'] }).items;

    setup(playlist);

    expect(screen.getByText('5m')).toBeInTheDocument();
    expect(screen.getByText('0 items')).toBeInTheDocument();
  });

  it('omits the interval when it is empty', () => {
    setup(getPlaylist(undefined, { interval: '' }));

    expect(screen.getByText('0 items')).toBeInTheDocument();
    expect(screen.queryByText('|')).not.toBeInTheDocument();
  });

  it('renders a loading skeleton without the start action', () => {
    jest.spyOn(contextSrv, 'hasPermission').mockReturnValue(true);
    const { container } = render(
      <TestProvider>
        <PlaylistCard.Skeleton />
      </TestProvider>
    );

    expect(screen.queryByRole('button', { name: /start/i })).not.toBeInTheDocument();
    expect(container.querySelectorAll('.react-loading-skeleton').length).toBeGreaterThanOrEqual(3);
  });
});
