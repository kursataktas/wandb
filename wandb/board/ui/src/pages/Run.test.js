import React from 'react';
import MockAppWrapper from '../util/test/mockAppWrapper';
import {Run} from './Run';
import {Loader} from 'semantic-ui-react';
import RunViewer from '../components/RunViewer';
import RunEditor from '../components/RunEditor';

describe('Run page components test', () => {
  const store = mockStore({
      global: {},
      views: {
        server: {},
        browser: {
          run: {
            views: [],
            tabs: [],
          },
        },
        other: {
          run: {
            activeView: '',
          },
        },
      },
    }),
    model = {
      bucket: {
        createdAt: '2017-24-09T10:09:28.487559',
        exampleTable: '[]',
        exampleTableColumns: '[]',
        exampleTableTypes: '{}',
        history: [],
        logLines: {
          edges: [],
        },
        summaryMetrics: '{}',
      },
    },
    loss = [],
    user = {};
  let container,
    loading = true,
    match = {
      params: {
        run: '',
      },
      path: '/:entity/:model/runs/:run',
    };

  beforeEach(() => {
    container = shallow(
      <Run
        match={match}
        model={model}
        bucket={model.bucket}
        loss={loss}
        user={user}
        loading={loading}
        updateLocationParams={() => {}}
      />,
    );
  });

  it('finds <Loader /> component', () => {
    expect(container.find(Loader)).to.have.length(1);
  });

  it('finds <RunViewer /> component', () => {
    window.Prism = {
      highlightAll: () => {},
    };
    expect(container.find(RunViewer)).to.have.length(0);
    container.setState({model: model, bucket: model.bucket});
    expect(container.find(RunViewer)).to.have.length(1);
  });
});
